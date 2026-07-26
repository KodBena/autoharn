# FABLE-DISCHARGE-PROBES-SPEC — best-effort probes against "likely superseded"

<!-- doc-attest-exempt: Fable-authored spec 2026-07-25, commissioned ledger rows 1284/1286
(the maintainer: "feel free to write it up as a small Fable spec; it should be a
best-effort thing and not mandatory just keep that in mind"). Awaiting his yes/no.
Removal condition: superseded by the build's completion record or declined. -->

- **Status:** Fable-authored 2026-07-25, awaiting maintainer yes/no.
- **The problem, his words (row 1284):** *"Can we build a mechanic gate so that 'likely
  superseded' is no longer possible?"* — an open work item's continued relevance today
  lives in orchestrator recall; when delivered-elsewhere work discharges an item's need,
  nothing notices mechanically.
- **The posture, his words (row 1286):** *"a best-effort thing and not mandatory."*
  Nothing here blocks, gates, or refuses anything. Probes are optional; the sweep is
  advisory; every output is a report for a human.

## 1. The probe declaration

An open work item MAY carry a discharge probe: one additional ledger row (`kind=note`,
`--refs` the work item's row) whose statement has the fixed shape:

```
discharge-probe: <one-line command> => <expected observation> -- <one-line reading>
```

Example, the retroactive specimen (the item this mechanism was commissioned over):

```
discharge-probe: ./autoharn led --recent 1 --refuse-demo => a typed write_refused row visible
  via led show -- if refusals are already durable typed ledger rows, this item's
  server-log tier is redundant
```

Rules, each one line:
- The command is **read-only by contract**: it may run repo verbs in read modes and
  SELECT-shaped queries; a probe that writes anywhere is a defect of the probe.
- Probes are **code**: they enter through the ordinary commit path (a probe registry
  file, §3) and get the ordinary review a script gets. The ledger row cites the
  registry entry; the sweep executes only registry entries, never raw ledger text —
  ledger statements are data, and data is never executed (the fixture-leak lesson,
  rows 1237–1248, applied in advance).
- An item with no probe is fine (best-effort). The sweep lists it as UNPROBED so the
  gap is visible, never silent — a listing, not a nag and not a refusal.

## 2. The sweep

A read-only verb (working name `./autoharn probe-sweep`; final name at build) that:
1. enumerates open work items;
2. for each with a registered probe, runs it against a scratch or read-only surface and
   compares the observation to the expectation;
3. reports three buckets, one line each: **HOLDS** (need still unmet — item stands),
   **PROBE-WITNESSED-SUPERSEDED** (expected observation seen — candidate for closure,
   observed output attached verbatim), **UNPROBED**;
4. writes nothing. A PROBE-WITNESSED-SUPERSEDED line becomes a closure only when the
   maintainer (or the orchestrator, for items inside its ordinary authority) closes the
   item citing the sweep's observed output as `--witness`.

The judgment split, per the maintainer's own framing: encoding a gate into something
checkable is human/LLM judgment, exercised once at declaration; *evaluation* is
mechanical; *confirmation* stays human. "Likely superseded" becomes
"probe-witnessed, here is the output, confirm or overrule."

## 3. One home

`tools/discharge_probes/registry.py` — a plain data module (no lazy imports): probe id →
{command argv, expected-observation matcher, one-line reading, work-item slug}. The
sweep verb reads it; the ledger note points at it; review reads it like any code.
The matcher vocabulary starts closed and small (exit-code is N; stdout contains S;
stdout matches anchored regex R) — extended by ordinary commits when a real probe
needs more, never speculatively.

## 4. What this is not

Not a gate (nothing blocks on a probe result). Not mandatory (UNPROBED is a legal
steady state). Not a scheduler and not prioritization — the signed-predicate question
(row 1285) is a SEPARATE commission currently under adversarial consult; if that arc
later wants probes as one input, it composes by reading the same registry, and nothing
here presupposes it.

## 5. Discharged by (the appendix lesson, applied)

- Declaring a probe: whoever opens or touches the item — orchestrator in practice —
  judgment applied once at encoding time.
- Running the sweep: the orchestrator, routinely (e.g. at backlog reviews); any
  operator, freely — it is read-only.
- Confirming a supersession: the maintainer, except items already inside the
  orchestrator's ordinary closure authority, which he closes citing the observed output.

## 6. Witness plan (build-time)

Registry with ≥3 real probes for currently-open items (each probe's command run
red/green: expectation unmet on a world where the need stands, met on one where it is
delivered — scratch worlds); the sweep's three buckets each witnessed non-empty; the
write-nothing property witnessed (ledger row count identical before/after a sweep);
a probe that attempts a write refused by review, banked as the seen-red specimen.
Sonnet-buildable on ratification; no kernel change; strengthened review (it executes
registry code, so the registry-not-ledger-text boundary is the load-bearing line).

## License

Public Domain (The Unlicense).
