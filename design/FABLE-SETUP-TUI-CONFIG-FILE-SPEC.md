# FABLE-SETUP-TUI-CONFIG-FILE-SPEC — loadable world configurations

<!-- doc-attest-exempt: commissioned build basis, frozen 2026-07-22 (maintainer commission,
verbatim seed below). Construction reads from this file as-frozen; A:B:C prose-polish runs
separately against a live edition per the build-basis precedent. Removal condition: strike
when a polished live edition supersedes this. -->

- **Status:** Commissioned build basis (Fable-authored 2026-07-22).
- **Commission, the maintainer's verbatim words:**

```
I'd like you to investigate how I configured the "blank" world (except for the silly
stuff that borked) and save it as a "loadable configuration file" that I can apply to
any new project using basically 2 parameters : world name (and if it exists, should
reject) and directory name. So, the same TUI script would therefore also have a new
--from-config or something like that. Probably we'll also want it to be used as an
initial template (--initial-config so that the user may edit options individually from
a "known good configuration")
```

## 1. The config file

- **Format: TOML** (the deployment tree's existing idiom — panel.toml, boundary
  multiplex). Human-edited as writing, commented per key.
- **Content: keyed decisions, not positional answers.** Keys are the wizard's own
  decision identifiers (the state keys its screens produce — feature selections, daemon
  selections, ADR adoptions, principal roster choices, substrate options), grouped by
  screen section. The positional `--scripted` answers file is unchanged and remains the
  witness harness's tool; the config file is the *operator's* artifact.
- **Excluded by type, never present in a config:** world name, destination directory,
  and anything machine- or instance-specific (host paths resolved at run time, generated
  keys, secrets, timestamps). A config with such a key is REFUSED loudly, not cleaned.
- Header carries `config_format = 1`, a `produced_by` note, and the source (which world
  or run it was captured from).

## 2. The two consumption modes

- **`--from-config FILE --world NAME <dest-dir>`** — non-interactive application. The
  two CLI parameters are the ONLY per-project variables; everything else comes from the
  file. Complete-or-refuse: a config missing a key the flow needs REFUSES up front,
  naming every missing key at once (no mid-flow interactive fallback — a rehearsed
  config must be deterministic). Unknown keys likewise refuse loudly (a typo must not
  silently become a default).
- **`--initial-config FILE`** — interactive run, config values pre-loaded as each
  prompt's default (the "known good configuration" the operator edits individually).
  Partial configs are fine here; missing keys simply keep normal defaults. Navigation
  (obs e machinery) works as usual.

## 3. Rejection rules for the two parameters

- **World name:** REFUSED if the schema (or `<name>_kernel`) already exists on the
  target Postgres, or if the destination's sentinel names a different world — checked
  before any act, with the existing-world's identity named in the refusal.
- **Destination directory:** classified through the one existing Port
  (`classify_destination`); anything but FRESH follows that spec's existing refusal
  paths and flags — this spec adds no second opinion on destinations.

## 4. Self-application: every birth saves its config

At commit, the wizard writes the resolved decision set as `world-config.toml` into the
destination (alongside the journal). That file IS the loadable artifact — "save a known
good configuration" becomes a property of every birth, not a one-off archaeology. The
capture excludes the §1 excluded-by-type keys by construction. (The blank-world config
this commission starts from is recovered by archaeology once; nobody should ever have
to do that again.)

## 5. The shipped exemplar

`bootstrap/templates/known-good-blank.toml`: the maintainer's blank-world configuration,
reconstructed from the blank tree's own record (journal, deployment.json, apparatus,
checklist output), MINUS the defects the field test exposed (nothing that borked is
canonized: no unverified-genesis override, no manually-started daemons workaround —
the config expresses the intent, today's fixed flow supplies the mechanics). Shipped
committed, used by the fixtures, and usable directly as `--initial-config`.

## 6. Witness plan

- New fixture `seen-red/setup-tui-config-file/`: (i) `--from-config` full dry-run birth
  from the exemplar, deterministic, zero prompts; (ii) missing-key refusal names all
  missing keys (red first); (iii) unknown-key refusal (red first); (iv) world-exists
  rejection on both the schema and sentinel legs; (v) `--initial-config` scripted leg
  proving a config default can be individually overridden at the prompt; (vi) round-trip
  — a birth's saved `world-config.toml` re-applied via `--from-config` reproduces the
  same resolved decision set (the self-application property, checked mechanically).
- Scripted-smoke stays 13/13 untouched; all four gates green; purity gate governs any
  new emission (typed elements only).
