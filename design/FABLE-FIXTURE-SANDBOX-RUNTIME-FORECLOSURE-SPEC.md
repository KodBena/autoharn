# FABLE-FIXTURE-SANDBOX-RUNTIME-FORECLOSURE-SPEC — the verbs refuse the fixture, not the census

<!-- doc-attest-exempt: Fable-authored spec 2026-07-26, commissioned ledger rows 1315/1316
(maintainer disposition on the non-converging pin-guard review loop: "I'll take your
recommendation" — demote the static gate to a detector, commission this as the guarantee).
Awaiting his yes/no. Removal condition: superseded by the build's completion record or
declined. -->

- **Status:** Fable-authored 2026-07-26. RATIFIED via the maintainer's acceptance of the
  row-1316 recommendation, confirmed same day ("make a decision on your own") — no separate
  yes/no owed; the orchestrator queuing one anyway was excess ceremony, corrected on the
  record (row 1325). Build proceeds; scheduled serially behind the deploy-feature-manifest
  merge because both sweep `seen-red/*/run_fixtures.py`.
- **The class (rows 1237–1248):** a fixture invokes this repo's own root verbs, or mutates
  `PICKUP_DEPLOYMENT`, and test garbage lands in the real ledger.
- **Why static detection cannot close it (rows 1315/1316, witnessed five times):** a
  commit-time AST census must enumerate spellings, and the unenumerated remainder passes
  silently; the strict complement would refuse ~75 benign wrapper-idiom files. The census
  (`gates/fixture_deployment_pin_guard.py`) is therefore demoted to a fast-feedback
  detector. The guarantee moves here: **enforcement stops depending on recognizing the
  call and starts depending on the called thing refusing.** Every spelling — `os.system`,
  keyword argv, `match/case`, spellings nobody has invented yet — hits the same refusal,
  because the refusal is in the verb, not in a parser looking for the verb.

## 1. The marker

Every fixture entry point (`seen-red/*/run_fixtures.py`, per the census registry) sets
`AUTOHARN_FIXTURE_SANDBOX=1` in its own process environment at the top of the module,
before any subprocess is spawned. Environment inheritance does the propagation: any
process tree a fixture starts carries the marker for free, however indirectly it was
spawned.

## 2. The refusal

This repo's own root verb surface — the `./autoharn` dispatcher and `libexec/autoharn/*`
(one shared preamble; the pre-umbrella `./verb` alias shims inherit it by dispatching) —
checks the marker before doing anything. Marker present → typed refusal with teaching:
what the fixture tried, why it is refused (rows 1237–1248, this spec), and both sanctioned
exits (scratch worlds; the waiver below). Exit code distinct and documented.

**Scoped deliberately to the repo-root surface.** A scratch world's own `./led` (the
served shim a fixture scaffolds via `new-project.sh`) does NOT refuse under the marker —
fixtures legitimately drive scratch worlds; that is the house pattern, and the incident
class was never about scratch. The line is: verbs bound to THIS repo's deployment refuse;
verbs bound to a world a fixture built for itself do not.

## 3. The waiver

`AUTOHARN_FIXTURE_SANDBOX_WAIVER="<reason>"` — set explicitly by a fixture that has a
reviewed need to touch a repo-root verb (the `freeze-at-stamp` snapshot cases are today's
two known specimens). The reason string is mandatory, echoed by the verb into its output
so the run's transcript carries the justification at the use site. An empty reason
refuses.

## 4. Keeping the marker honest

`gates/fixture_census.py` (already the registry of every fixture entry point) gains one
additive check: a registered `run_fixtures.py` that does not set the marker is a census
failure. Mechanical, fail-safe, no new gate.

## 5. What this is not

Not a sandbox in the OS sense (no seccomp, no namespaces — a hostile fixture can unset
the variable; the adversary here is the accident, not the attacker, same threat model as
every gate in the chain). Not a change to any world's verbs. Not a replacement for the
demoted census gate, which stays as commit-time fast feedback for the common spellings.

## 6. Witness plan (build-time, red first)

(1) Marker set, fixture invokes `./autoharn led` → typed refusal with teaching, banked
red. (2) Same with `os.system`/keyword-argv/`match-case` spellings — the census gate's
own five-lap evasion specimens rerun against the runtime refusal, each refused (the point
of the whole design, witnessed on the exact shapes static analysis missed). (3) Waiver
with reason → proceeds, reason echoed in output. (4) Empty-reason waiver → refused.
(5) The non-false-positive leg: a fixture-scaffolded scratch world's own `./led` works
normally under the marker. (6) Census check red/green: a registered fixture without the
marker fails the census. Sonnet-buildable on ratification; touches the shim preamble +
fixture_census + every run_fixtures.py (mechanical one-line addition, its own commit).

## License

Public Domain (The Unlicense).
