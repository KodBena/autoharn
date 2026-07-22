# ADR-0019 Appendix (PROVISIONAL) — twenty UI proscriptions, blind-consult edition

<!-- doc-attest-exempt: provisional appendix installed verbatim from an independent
codebase-blind Opus consult, 2026-07-22, at the maintainer's instruction. Removal
condition: superseded by ratification into ADR-0019 proper, or struck by the maintainer. -->

**Status: PROVISIONAL GUIDANCE, not ratified law** (maintainer, 2026-07-22, verbatim:
"that document could go into our project as guidance; I'm not ready to make it law just
yet, but it could be a provisional law, until I decide the results do not prove to
contradict what I want while obeying the 20 points (and I also wouldn't want entries
that are never enforced, either, so we'd have to see; so: provisional appendix to
ADR-0019, separate file, is what I think, for now)").

Standing consequences of PROVISIONAL status: builders and reviewers treat these twenty
points as binding defaults for new UI work; a conflict between a point and what the
maintainer actually wants is surfaced to the maintainer, never resolved silently in
either direction, and is evidence for the eventual ratify-amend-or-strike decision.
A point that goes unenforced in practice is a cull candidate at ratification time —
the named-consumer test applies to law too. Provenance: phase 1 of a two-phase consult
(codebase-blind Opus instance; the phase-2 critique/consolidation against the sighted
consult of the same day is a separate document, design/CONSULT-OPUS-*, and informs the
ratification decision when the maintainer takes it up). The consult text below is
verbatim and unedited.

---

# UI Failure Proscriptions for Vue SPA and Textual TUI Substrates

*Independent consult, phase 1. Codebase-blind by construction — every rule below is drawn
from the HCI/UX/software-engineering literature and from the two named substrates' documented
capabilities, not from any project artifact.*

---

## Organizing principle: what makes UI-failure knowledge distillable into law

Most UX wisdom cannot be law, because most of it quantifies over a *subjective experience in a
user's head* ("intuitive," "delightful," "clear"). You cannot refuse a pull request for failing
to be intuitive without a taste debate, and you cannot mechanically detect it. The knowledge that
**is** distillable into law is the subset where the defect is a **decidable property of the
interface artifact or its state machine** — visible in the source, the render tree, the type
signatures, or the enumerable set of state transitions — such that a reviewer (or a linter, or a
type checker) can rule an instance in or out of the class *without running a user study*.

The transformation from heuristic to proscription is therefore always the same move: take a
positive heuristic that ranges over experience ("keep users informed of system status") and find
the **artifact-level invariant whose violation is the failure mode** ("a datum that can age is
rendered with no as-of time"). The heuristic supplies the *why* and the pedigree; the invariant
supplies the *decidable class*. Where that move can be pushed all the way to a type (the illegal
state cannot be constructed) it should be; where the honest maximum is human review, this document
says so plainly rather than dressing a review item as a gate.

A second filter runs underneath: the two substrates fail *differently*, and a rule earns its
cross-substrate note only where the binding genuinely differs. A Vue SPA renders to a DOM with an
accessibility tree, a pointer, arbitrary color, and a browser event loop; ARIA/WCAG tooling
(axe-core, stylelint, ESLint a11y plugins) is mature and CI-ready there. A Textual app renders to a
character grid over a terminal the operator controls: it is keyboard-native, its "pixels" are cells,
its color depth and background are *not* knowable at build time (and may be suppressed by
`NO_COLOR` or a 16-color terminal), and its concurrency story is the explicit `@work`/worker API.
Rules that are trivially satisfied on one substrate can be the dominant hazard on the other, and the
enforcement surface moves accordingly.

The enforcement ladder used throughout, strongest first:
**(1) construction-time typed refusal** (illegal state is unconstructable) >
**(2) load/startup-time validation with loud refusal** >
**(3) mechanical gate or lint in CI** >
**(4) human review only** (named as such when it is the honest ceiling).

---

## P1 — Irreversible mutation without a confirmation step or an undo path

**Proscription.** A UI action that mutates or destroys persistent state in a way not reversible by
a single subsequent UI action is refused at construction time unless it is routed through a command
type that carries either an explicit confirmation gate or a registered undo. A destructive control
that reaches the user without one of those two is a defect, not a preference. Confirmation and undo
are alternatives, not both required — but *neither* is refused.

**Class closed.** All state-mutating UI actions partitioned by reversibility: the class is
`{destructive actions} minus ({those guarded by a confirm step} union {those with a registered
undo})`. Reversibility is a property the author declares on the action, so membership is decidable
from the action's declaration, not from taste.

**Enforcement surface.** Construction-time typed refusal *if* all mutations flow through one command
dispatcher: model actions as a discriminated union where the `destructive` variant's constructor
demands a `confirm` or `undo` field — omission fails the type check. Where a legacy path still binds
handlers directly, the honest floor drops to a CI lint that flags mutating calls in templates/handlers
lacking the wrapper.

**Pedigree.** Nielsen heuristic #3 (user control and freedom; undo/redo) and #5 (error prevention);
Shneiderman's Golden Rule "permit easy reversal of actions"; Norman's forcing functions and
poka-yoke (*The Design of Everyday Things*); Cooper, *About Face* (the difference between good and
gratuitous confirmation).

**Substrate binding.** *Vue:* `@click` handlers on buttons are the leak site; enforce a typed
`dispatch(Command)` layer and an ESLint rule forbidding direct mutating calls in templates. *Textual:*
`Button.Pressed` handlers and `action_*` methods; a base `App`/`Screen` class can require that any
method decorated as destructive resolves through a confirm `Screen` push or an undo stack, checked
by a metaclass or a startup assertion over the action registry.

---

## P2 — Reporting success before the operation is durably acknowledged

**Proscription.** The UI is refused from entering a committed/success state before the operation's
authority has acknowledged durability. Optimistic rendering is permitted only when it is a *distinct,
labelled provisional state* with a defined rollback on failure; a success indicator set in the same
turn as the dispatch, with no acknowledgement edge, is forbidden. The interface may not lie about
what the backend has done.

**Class closed.** All transitions into a "done/saved/applied" presentation state: forbidden unless
the transition's only in-edges originate from an acknowledgement event. Decidable by inspecting the
state machine's edges into the terminal-success node.

**Enforcement surface.** Construction-time typed refusal via an explicit async state machine
(discriminated union `idle | pending | ack-success | ack-error`, or an XState-style chart): the
success node is unreachable except from the ack event, so "set success on dispatch" does not
type/compile. Lower floor: a lint forbidding assignment to success flags in the same lexical scope
as the dispatch call without an intervening `await`.

**Pedigree.** Nielsen #1 (visibility of *true* system status); Norman's Gulf of Evaluation; ISO
9241-110 conformity with user expectations; the distributed-systems maxim that an unacknowledged
write is not a write.

**Substrate binding.** *Vue:* reactive `ref`/`pinia` success flags flipped optimistically are the
hazard; forbid mutating them before the awaited promise resolves. *Textual:* forbid `post_message`
of a success/notify before the `@work` worker's completion event; worker `state` is the
acknowledgement source and must gate the render.

---

## P3 — Collapsing distinct async/data states into one presentation

**Proscription.** A view is refused from rendering a value in a way that makes the states *loading*,
*error*, *empty result*, *genuine zero*, and *no-data-yet* indistinguishable. Each must have a
presentation a viewer can tell apart. A dashboard that shows `0` when it means "the feed is down"
is a defect at the same severity as showing wrong data, because the operator will act on it.

**Class closed.** Every asynchronous or fallible data source rendered in the UI: the value must pass
through a state-tagged wrapper and the render must discriminate all arms. The class is "renders that
read a resource's payload without switching on its state."

**Enforcement surface.** Construction-time typed refusal: model remote data as a discriminated union
(`Loading | Error | Empty | Loaded<T>`); the payload `T` is only reachable inside the `Loaded` arm,
so a bare render of the value does not type-check. An exhaustiveness check (TS `never` / Python
`assert_never`) forces all arms handled.

**Pedigree.** Nielsen #1 (visibility) and #9 (recognize/diagnose/recover from errors); Norman's Gulf
of Evaluation; the null-vs-zero data-integrity tradition (Codd's treatment of NULL; the long-known
hazard of "nil punning" a missing value into a default).

**Substrate binding.** *Vue:* a `RemoteData<T>` type + exhaustive `v-if`/`v-else-if`; lint against
reading `resource.data` outside a state guard. *Textual:* a `reactive` holding the union; `render()`
must `match` on the state — the same discipline, enforced by the same exhaustiveness tooling.

---

## P4 — Presenting aging data without an as-of time and a distinct stale state

**Proscription.** Any operational datum whose value can age relative to its source is refused from
rendering without (a) a viewer-legible as-of/recency indication and (b) a visibly distinct degraded
appearance when the feed is stale or disconnected past a declared threshold. "Live-looking" data
that has silently frozen is the canonical control-room fatality mode and is forbidden.

**Class closed.** All time-varying metrics on operational panels: each metric-bearing component must
carry a freshness timestamp and a staleness threshold. Decidable from the component's props/inputs —
either the timestamp is there or it is not.

**Enforcement surface.** Construction-time typed refusal: the metric/gauge component type requires a
non-optional `asOf` (and a staleness policy); omission is a compile error. The stale-state rendering
is then a pure function of `asOf` vs now, testable in CI.

**Pedigree.** Nielsen #1 (visibility of system status); EEMUA 191 / ISA-18.2 alarm-and-display
management; the aviation "failure of the failure indicator" lesson; process-control HCI after Three
Mile Island; Tufte on graphical integrity.

**Substrate binding.** *Vue:* a required `asOf: Date` prop on metric components; a shared "last updated
/ STALE" chrome. *Textual:* a metric widget subclass requiring `as_of` in its constructor, with a
`reactive` that recomputes staleness on each refresh tick and restyles (dim/marker) when stale — note
the terminal cannot animate a "pulse," so the staleness signal must be a glyph/label, not motion.

---

## P5 — Encoding meaning in color alone

**Proscription.** A state distinction — status, validity, severity, selection — is refused from being
carried by hue alone. Every such distinction must have a redundant non-color channel: a text label, a
glyph/shape, or a position. Roughly one in twelve male operators cannot reliably separate the
red/green that operational panels lean on hardest.

**Class closed.** All semantic state distinctions in the render: each must resolve to at least one
non-hue channel. Decidable by inspecting whether the only differentiator between two states is a
color token.

**Enforcement surface.** Construction-time for the common case: a `Status` component type that will
not render without both a semantic token *and* a glyph+label. CI gate (axe-core "use of color"
family) catches ad-hoc cases in Vue. Some cases (color-only diffs in bespoke canvas/table cells)
remain review — say so.

**Pedigree.** WCAG 2.x SC 1.4.1 (Use of Color) and SC 1.4.11 (non-text contrast); Ware, *Information
Visualization*; ISO 9241; the color-vision-deficiency prevalence literature.

**Substrate binding.** *Vue:* a status-pill component enforcing icon+label; axe-core in CI. *Textual:*
the hazard is *sharper* — the terminal may be monochrome, may honor `NO_COLOR`, or may remap the
palette; Rich style-only status (e.g. `[green]` with no glyph) is doubly fragile. Forbid style-only
status; require a glyph/label; respect `NO_COLOR`.

---

## P6 — Text and essential glyphs below contrast threshold

**Proscription.** Text and information-bearing glyphs are refused from rendering below the WCAG
contrast thresholds (4.5:1 for normal text, 3:1 for large text and non-text UI) against their actual
background. Low-contrast "elegant" gray-on-gray is a defect, especially on the sunlit or projected
screens operational UIs run on.

**Class closed.** All text/essential-glyph foreground-background pairs: each must meet the threshold.
Decidable by computing the contrast ratio of the pair.

**Enforcement surface.** *Vue:* CI gate — token-level contrast test over the design palette plus
axe-core over rendered pages. *Textual:* the honest maximum drops, because the terminal background is
operator-controlled and unknown at build time. The enforceable rule there is: forbid *assuming* a
specific terminal background, forbid hardcoded absolute foreground colors that presume one, and
prefer theme/role colors that inherit the terminal's own fg/bg contrast contract; the residual is
review + a documented minimum-terminal assumption.

**Pedigree.** WCAG SC 1.4.3, 1.4.6 (enhanced), 1.4.11.

**Substrate binding.** Stated inline above — this is the archetypal rule that is a hard CI gate on
Vue and an honestly-review-bounded discipline on Textual, precisely because one substrate owns its
pixels and the other borrows the operator's terminal.

---

## P7 — Controls not operable by keyboard, and focus that cannot escape

**Proscription.** An interactive control is refused if it cannot be operated by keyboard alone, and
any focus state from which keyboard focus cannot leave by standard keys is refused. Operational UIs
are driven under load, gloved, or over SSH; a mouse-only control is an inaccessible control.

**Class closed.** Two decidable sub-classes: (a) interactive elements lacking keyboard operability
(handlers bound to non-interactive nodes, missing focusability); (b) focus traps — a focusable
region with no keyboard exit edge.

**Enforcement surface.** *Vue:* CI lint/gate — axe-core and `eslint-plugin-vuejs-accessibility`
(click handlers on non-interactive elements, positive `tabindex`, modal focus-trap must have an
escape). *Textual:* the substrate is keyboard-native, so class (a) inverts to "actions reachable only
via mouse events" and "focusable widgets unreachable in tab order"; enforce by asserting over the
binding/`can_focus` graph at startup that every action has a key path and no focus cycle lacks an
escape binding.

**Pedigree.** WCAG SC 2.1.1 (Keyboard) and SC 2.1.2 (No Keyboard Trap); Shneiderman (shortcuts for
frequent users); Raskin, *The Humane Interface*.

**Substrate binding.** Stated inline: Vue must *earn* keyboard access the DOM does not give for free;
Textual gets it for free and must instead not *lose* it by hiding function behind mouse-only events.

---

## P8 — Discarding user-entered input on error or navigation

**Proscription.** A flow is refused from discarding operator-entered data on validation failure, a
transient error, or navigation-away without either preserving that input or interposing an explicit
unsaved-changes guard. Re-typing a config the machine already had is the interface wasting the
operator's most expensive resource — attention already spent.

**Class closed.** Two decidable sub-classes: (a) validation/error handlers that reset the input model
instead of returning errors alongside the preserved input; (b) navigation/exit edges out of a dirty
editor with no guard.

**Enforcement surface.** (a) Construction-time-leaning: the validator returns
`errors + original input`, and clearing the model on failure is not on the type's surface. (b) CI
gate: editor routes/screens must register a leave guard; absence fails the gate.

**Pedigree.** Nielsen #5 (error prevention) and #3 (control); Shneiderman "reduce short-term memory
load"; Wroblewski, *Web Form Design*.

**Substrate binding.** *Vue:* `beforeRouteLeave` + `beforeunload` on dirty forms; validation must not
reset `v-model` state. *Textual:* the `App` quit path and screen-pop must run a dirty check before
discarding an editor `Screen`; `Input` widgets must retain their value on validation failure rather
than clearing.

---

## P9 — Applying configuration without prior validation and atomicity

**Proscription.** A configuration editor is refused from committing operator input to the live target
without (a) validating it against the target's schema/constraints *before* commit and (b) applying it
atomically — a partial write on failure is forbidden, the target is left either fully-old or
fully-new. The "apply" path must consume a value that could only have been produced by the validator.

**Class closed.** Every commit-to-target action in a config editor: forbidden unless its input is a
validated (branded) type and its write is transactional. Decidable from the apply function's input
type and its write strategy (all-or-nothing vs incremental).

**Enforcement surface.** Construction-time typed refusal via *parse-don't-validate*: `apply()` accepts
only `Validated<Config>`, a branded/opaque type whose sole constructor is the validator, so applying
unvalidated input does not type-check. Atomicity is a load-time property of the write path (temp +
atomic swap, or a transaction), assertable in tests. Disabling the button is *not* sufficient and is
explicitly not the required control.

**Pedigree.** Alexis King, "Parse, don't validate"; Norman's error prevention / forcing functions;
Nielsen #5; the atomic-configuration tradition (etcd, Nix generations, ACID) — and this rule bears
most directly on the config-editor genre named in the commission.

**Substrate binding.** *Vue:* `apply` typed to the branded config; client-side validation is a
convenience, the authoritative validate+atomic-write is the contract the UI must not bypass.
*Textual:* the same typed gate on the Python action; forbid writing the config file when validation
of the whole document has not passed, and write via temp-file + atomic rename, never in place.

---

## P10 — Blocking the UI thread during long work

**Proscription.** An operation is refused from executing on the render/event thread when it can exceed
the human response-time thresholds (~0.1 s = "instant," ~1 s = unbroken flow, ~10 s = attention
limit) such that input freezes. A frozen operational panel during an incident is worse than a slow
one, because the operator cannot tell it apart from a crash.

**Class closed.** All potentially-slow operations (network, disk, heavy compute) invoked from an event
handler synchronously. Decidable by static detection of blocking calls on the UI thread.

**Enforcement surface.** CI lint (ban synchronous network, `time.sleep`, and known-heavy calls inside
handlers) plus a typed nudge: route long work through an async/worker primitive whose result is the
only way back into state. Not fully construction-time (a hand-rolled loop can still block), so the
honest floor is lint + review for compute-bound loops.

**Pedigree.** R.B. Miller (1968) response-time thresholds; Nielsen's response-time limits; Card/Moran/
Newell; Shneiderman.

**Substrate binding.** *Vue:* forbid synchronous XHR and heavy synchronous compute in handlers; offload
CPU to a Web Worker; the event loop is single-threaded so any block freezes the frame. *Textual:*
the substrate hands you the answer — `@work(thread=True)` for blocking IO, `@work` for async — so the
lint is precisely "no blocking call inside a message handler or `compose`; it belongs in a worker."

---

## P11 — No progress feedback past the response-time thresholds

**Proscription.** An operation is refused from crossing ~1 s with no busy indicator, or ~10 s with no
*determinate* progress indication where progress is knowable. This is distinct from P10: a correctly
non-blocking operation can still leave the operator staring at an unchanged screen, unable to
distinguish "working" from "hung."

**Class closed.** All operations whose latency can exceed the thresholds: each must surface a
busy/progress state bound to its lifecycle. Decidable from whether the operation's pending state is
rendered.

**Enforcement surface.** Construction-time-leaning when P2/P3's state machine is in force — the
`pending` arm exists and the render must handle it, so an unrendered pending state fails the
exhaustiveness check. Otherwise CI lint / review that awaited operations expose a pending binding.

**Pedigree.** Miller (1968); Nielsen response-time limits and heuristic #1; Shneiderman "offer
informative feedback."

**Substrate binding.** *Vue:* a spinner/progress bound to the `pending` state; suspense/loading
boundaries. *Textual:* `LoadingIndicator`, `ProgressBar`, or a footer status bound to worker state;
because the terminal cannot show a busy cursor, the in-panel indicator is the *only* signal and its
absence is more acute than on the web.

---

## P12 — Long or side-effecting operations with no cancel

**Proscription.** An operation past ~10 s, or one with observable side effects that runs longer than
instantaneously, is refused from being offered without a cancel/abort affordance wired to actually
stop the work. "Start" without "stop" strands the operator when they realize the parameters were
wrong.

**Class closed.** All long-running or side-effecting operations exposed in the UI: each must be
cancellable. Decidable from whether the operation's runner accepts and honors a cancellation token.

**Enforcement surface.** Construction-time-leaning: the long-op runner's signature requires a
cancellation token (`AbortSignal` / worker handle), so a non-cancellable long op cannot be
constructed through the sanctioned runner; residual review for work that ignores the token it was
given.

**Pedigree.** Nielsen #3 (user control and freedom — "emergency exit"); Shneiderman "support internal
locus of control"; Miller thresholds.

**Substrate binding.** *Vue:* `AbortController` plumbed through fetch and exposed as a cancel control.
*Textual:* Textual workers are cancellable by design (`Worker.cancel`, `workers.cancel_all`) — the
rule is to *expose* that cancel to the operator and to write workers that check their cancelled
state at safe points, not to leave cancellation available only to the framework.

---

## P13 — Silent failure: swallowed errors

**Proscription.** An error or exception path is refused from returning the UI to an apparently-nominal
state without surfacing a diagnosable message and, where one exists, a recovery action. An empty
catch, or a catch that only logs and continues, is forbidden in UI code. Failures must be loud at the
surface the operator is watching, not only in a log they are not.

**Class closed.** All error-handling constructs in UI code: forbidden if they neither rethrow nor
surface a user-visible, diagnosable error. Decidable by static inspection of catch/except bodies and
of unhandled-rejection wiring.

**Enforcement surface.** CI lint (ban `catch {}` / `except: pass` / catch-and-only-log in UI modules)
plus a typed floor where feasible: a `Result<T, E>` return forces the caller to handle `E`. A global
error boundary must exist and surface, not suppress.

**Pedigree.** Nielsen #9 (help users recognize, diagnose, recover from errors) and #1; ISO 9241-110;
the engineering tradition that a swallowed exception is a latent defect.

**Substrate binding.** *Vue:* `app.config.errorHandler` and per-component error boundaries that render
a visible error; forbid silent catches in components and unhandled promise rejections. *Textual:* the
`App`-level exception hook must surface (notify/screen), worker exceptions must not be swallowed, and
`except: pass` in handlers is banned.

---

## P14 — Error messages that locate nothing and suggest nothing

**Proscription.** A validation or error presentation is refused if it reports failure without (a)
locating the offending input and (b) stating what would make it valid. "Invalid configuration" with
no field and no remedy is a defect; it converts a two-second fix into a hunt.

**Class closed.** All user-facing error/validation messages: each must carry a location reference and
a remediation. Decidable from the error object's fields.

**Enforcement surface.** Construction-time typed refusal: the validation-error type requires
`{ location, message, remediation }` — an error missing a field cannot be constructed. Rendering then
places it against the located input.

**Pedigree.** Nielsen #9; WCAG SC 3.3.1 (Error Identification) and SC 3.3.3 (Error Suggestion);
Shneiderman "offer informative feedback"; Wroblewski on inline validation.

**Substrate binding.** *Vue:* the error component requires a field reference and a suggestion; wire
`aria-describedby`/`aria-invalid` so assistive tech reaches it too. *Textual:* the `Validator`'s
`Failure` carries a description; render it adjacent to the offending `Input` and announce it, not in a
detached banner.

---

## P15 — Placeholder-as-label and unlabelled inputs

**Proscription.** An input is refused if its only label is placeholder text that disappears on entry,
or if its label is not programmatically associated with it. A config field whose name vanishes the
moment the operator starts typing forces them to clear the field to recall what it was.

**Class closed.** All inputs: each must have a persistent, associated label distinct from any
placeholder. Decidable from the input's markup/label association.

**Enforcement surface.** CI gate: axe-core / `eslint-plugin-vuejs-accessibility` require a
programmatic label and flag placeholder-only inputs. On Textual the analogue is asserting each
`Input` has a `Label` or `border_title` and is not relying on `placeholder` as its name.

**Pedigree.** WCAG SC 1.3.1 (Info and Relationships), SC 3.3.2 (Labels or Instructions), SC 2.4.6
(Headings and Labels); the placeholder-usability research popularized by Wroblewski and Nielsen
Norman Group.

**Substrate binding.** *Vue:* every input has a `<label for>` (or `aria-label`); placeholder is hint,
never name. *Textual:* pair each `Input` with a visible `Label`/`border_title`; `placeholder` is a
hint, and note it also vanishes on entry in the terminal exactly as in the DOM.

---

## P16 — Auto-refresh that clobbers in-progress interaction

**Proscription.** An auto-updating view is refused from mutating content under the operator's active
focus, selection, or scroll position, or from resetting in-progress input on refresh. A panel that
yanks the row out from under a click, or wipes a half-typed filter every five seconds, actively
fights the operator.

**Class closed.** All timer/stream-driven refreshes: forbidden unless they pause or diff-preserve
around active interaction (focused control, selection, dirty input, scroll anchor). Partly decidable:
the presence of an interaction guard on the refresh path is checkable; whether the guard is
*complete* is review.

**Enforcement surface.** CI lint that refresh timers consult an interaction/dirty guard, plus review
for correctness of the guard. Honest maximum: gate on the guard's presence, review its adequacy.

**Pedigree.** Nielsen #1 (visibility) held in tension with #3 (control); Shneiderman "support internal
locus of control"; live process-monitoring HCI.

**Substrate binding.** *Vue:* reactive/websocket refreshes must not overwrite a dirty form or reset an
active selection; pause updates while editing, or reconcile without moving focus. *Textual:*
`set_interval` refreshes must not steal focus or reset an `Input`; a `DataTable` refresh must preserve
cursor/selection rather than rebuilding from scratch.

---

## P17 — Undifferentiated alarm/notification floods

**Proscription.** An operational dashboard is refused from presenting alarms or notifications without
severity prioritization and flood/rate suppression, such that a critical signal is buried or made
indistinguishable from noise. Alarm fatigue is a documented cause of operators disabling the very
signal that would have warned them.

**Class closed.** All alarm/notification sinks on a panel: each item must carry a severity, and the
sink must prioritize and rate-limit by it. Decidable that severity is required and that an ordering/cap
policy exists; the tuning of thresholds is review.

**Enforcement surface.** Construction-time for the required severity (an alarm without a severity enum
cannot be constructed) plus a load-time policy assertion that the sink sorts/caps by severity. Residual
review on threshold tuning — named as review.

**Pedigree.** EEMUA 191 and ANSI/ISA-18.2 (alarm management); the Three Mile Island and process-control
alarm-flood literature; Endsley on situation awareness; Nielsen #8 (aesthetic and minimalist — signal
over noise).

**Substrate binding.** *Vue:* the alarm-feed component requires severity, dedupes, and rate-limits;
critical alarms are visually and positionally dominant. *Textual:* the same in the panel, with
`notify` severity used deliberately rather than firing a toast per event; the narrow terminal makes
prioritization and capping *more* necessary, not less.

---

## P18 — Styling and controls outside the sanctioned design system

**Proscription.** A color, spacing, or interactive control is refused if it is instantiated with
raw/ad-hoc values outside the project's sanctioned design tokens and component set. Consistency is not
an aesthetic preference here; it is what lets an operator transfer a learned control from one panel to
the next without relearning, and it is the substrate on which every other rule above is enforced once
rather than per-widget.

**Class closed.** All styling values and control instantiations: forbidden if they use raw literals
(hex colors, magic spacing, hand-rolled buttons) instead of the token/component vocabulary. Decidable
by static detection of literals outside the sanctioned set.

**Enforcement surface.** CI lint/gate: stylelint (and equivalent) forbidding raw hex/px outside the
token set and forbidding ad-hoc controls where a design-system component exists. This is where P1/P4/
P5/P14 become enforceable *by construction*, because the sanctioned components are the ones that carry
the confirm gate, the as-of prop, the glyph+label, the structured error.

**Pedigree.** Nielsen #4 (consistency and standards); ISO 9241-110 (conformity, consistency); the
design-system tradition (Frost, *Atomic Design*; the tokens/components discipline).

**Substrate binding.** *Vue:* stylelint bans raw hex/px outside tokens; only design-system components
are permitted for the covered controls. *Textual:* Textual CSS (TCSS) with theme variables only — ban
inline hardcoded style literals in favor of `$`-variables, which *also* satisfies P5/P6 by inheriting
the theme's color-and-contrast contract instead of asserting absolute colors.

---

## P19 — Undersized pointer targets

**Proscription.** A pointer target is refused from rendering below the minimum interactive size (WCAG
2.5.8 baseline 24×24 CSS px; 44×44 at AAA) unless an equivalent larger hit area is provided. A control
too small to hit reliably becomes a control hit *wrong* — and on a destructive control that is P1's
hazard delivered by a mis-click.

**Class closed.** All pointer targets: each must meet the minimum size or spacing exemption. Decidable
by computing rendered target dimensions.

**Enforcement surface.** *Vue:* CI gate — computed-size assertions / axe target-size checks. *Textual:*
the honest maximum is lower and the severity is lower: the substrate is keyboard-first and its unit is
the character cell, so the rule reduces to "mouse-clickable regions should span enough cells to be hit,
and dense clickable rows need separation" — a review item with a modest lint on obviously 1-cell
click targets.

**Pedigree.** Fitts's Law (1954); WCAG SC 2.5.5 (Target Size, Enhanced) and SC 2.5.8 (Minimum); the
touch-target guidance in the Apple HIG and Material Design.

**Substrate binding.** Stated inline — a hard CI gate on Vue, a low-severity review-bounded rule on
Textual, and this asymmetry is itself the honest reporting the ladder demands.

---

## P20 — Modes without a persistent, visible indicator

**Proscription.** An interface mode that changes the effect of the same input is refused from existing
without a persistent, always-visible indication of which mode is active. Mode errors — the operator
issuing the right input into the wrong mode — are a distinct and well-catalogued failure class, and
the fix is either to remove the mode or to make its state impossible to lose track of.

**Class closed.** All modes (states in which identical input maps to different effects): each must bind
to an always-visible indicator. Partly decidable — that a mode enum has a rendered indicator binding is
checkable; that the indicator is *actually always visible and legible* is review.

**Enforcement surface.** Construction-time for the binding (a mode enum without a registered indicator
binding fails a startup assertion) plus review for the indicator's persistence/legibility. Honest
maximum here is a gate on the binding's existence with review on its adequacy; where a mode can be
removed entirely (Raskin's modelessness), removal outranks indication.

**Pedigree.** Raskin, *The Humane Interface* (modes and quasimodes, the case against modes); Norman on
mode errors and slips; Tesler (the law of conservation of complexity, and his lifelong campaign
against modes).

**Substrate binding.** *Vue:* modal editing states must drive a persistent indicator; forbid hidden
global mode flags that silently change what a keypress does. *Textual:* Textual's screen "modes" and any
vi-style key layers must surface the active mode in the footer/header; forbid bindings that silently
change meaning with no on-screen tell — the footer binding display is the natural, and required,
indicator surface.

---

*End of proscriptions. Where a rule's honest enforcement ceiling is human review (P16's guard
adequacy, P17's threshold tuning, P19 on Textual, P20's indicator legibility), it is marked as such
rather than overstated; the remainder reach a mechanical gate or a construction-time type, and the
document names which.*
