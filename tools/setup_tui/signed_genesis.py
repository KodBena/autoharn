#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T01:39:25Z
#   last-change: 2026-07-19T03:44:06Z
#   contributors: ab5d5bab/main
# <<< PROVENANCE-STAMP <<<

"""tools/setup_tui/signed_genesis.py -- the "Signed genesis" ceremony driver
(design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md, commission ledger rows 1724/1725). ONE home
(ADR-0012 P1) for every gpg/led act `screens.py`'s `screen_signed_genesis` orchestrates -- the
same pghba.py/probes.py split screens.py already uses for screens 2/6, applied to this new
screen: screens.py stays thin (ui prompts, checklist rows), this module carries the driver
logic. Every act here goes through `runner.run_command`/`runner.write_file` (rule 1's exact-argv
discipline + the `--dry-run` choke point), same as every other screens.py helper module.

SCOPE DISCIPLINE (the parent spec's build conditions -- "no changes to verify-commission/
verify-chain/gpg_trust.py semantics ... TUI stays a driver of existing verbs"): this module
drives the ALREADY-SHIPPED GPG trust layer (design/MAINT-GPG-TRUST-LAYER.md,
bootstrap/templates/verify-commission.tmpl, filing/gpg_trust.py) -- no second crypto stack, no
new tooling choice. Where this module needs a read verify-commission.tmpl itself already
performs (fetching a commission row's exact statement bytes by id -- the byte-fidelity signing
ceremony needs the SAME bytes verify-commission.tmpl will later hash), it mirrors that file's
OWN query shape verbatim (identical SET ROLE + row_to_json SELECT, so ambiguity about embedded
newlines never enters either side) rather than importing a `.tmpl`-suffixed script as a Python
library -- `fetch_commission_statement` below names this explicitly, once.

TWO VERBS, TWO MOMENTS, kept distinct throughout (spec §1 items 3-4):
  * `<dest>/legacy/led` -- this world's OWN direct-psql shim
    (bootstrap/templates/legacy-led.tmpl) -- lists/writes the genesis commission. Used
    DELIBERATELY instead of the rebased `<dest>/led`: this screen sits between Birth and
    Boundary in the flow (design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md §1's own ordering), and
    the rebased shim refuses outright without deployment.json's `boundary_url`/
    `boundary_deployment` keys (serving/boundary_cli_client.py `load_served_config`) -- keys
    `screen_boundary` writes LATER, not yet at this point. `legacy/led` needs neither (direct
    psql, exactly the "operator recovery when the boundary is down" shim design/
    FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §5 already ships for this reason), so this
    is the correct verb for THIS screen's position in the flow, not a workaround.
  * `<dest>/verify-commission` -- the ceremony's own gate (spec step 4). Only ever invoked,
    never re-implemented; `run_verify_commission` below is a thin subprocess wrapper, nothing
    more.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import here is top of file.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass

from tools.setup_tui import probes, runner
from tools.setup_tui.runner import CommandResult, run_command, write_file

# A throwaway, clearly-marked-test-only passphrase used ONLY under `--scripted` witnessing
# (spec §1 item 1: "a scratch GNUPGHOME with a fixture passphrase is used") -- never the
# operator's own path, which always gets gpg's own interactive pinentry prompt.
FIXTURE_PASSPHRASE = "setup-tui-fixture-passphrase-THROWAWAY-ONLY-never-a-real-key"

AWAITING_HEADER = "## Current state: AWAITING-KEY"
KEY_COMMITTED_HEADER = "## Current state: KEY COMMITTED"
# Marker pair (ledger row 1790, finding 1): ports durable_decisions.compile_claude_md's own
# BEGIN/END-marker idempotent-replace discipline to this file's "KEY COMMITTED" section --
# explicit markers around the discharged section, replace-only-the-middle on every run, bytes
# outside the markers never touched. Before this fix, a legitimate re-run (key rotation, or
# resume after a death between the README write and verification) recognized only the
# pre-discharge AWAITING-KEY shape and APPENDED a second "## Current state: KEY COMMITTED"
# section on any later run, leaving the first section false about the on-disk key's actual
# fingerprint.
KEY_COMMITTED_BEGIN = "<!-- BEGIN KEY COMMITTED SECTION (setup_tui signed_genesis) -->"
KEY_COMMITTED_END = "<!-- END KEY COMMITTED SECTION (setup_tui signed_genesis) -->"


def gpg_present() -> bool:
    return shutil.which("gpg") is not None


def key_filename(name: str) -> str:
    """A filesystem-safe `keys/<slug>.asc` name derived from the key's own Name-Real -- never a
    fixed literal (`maintainer.asc` in the FAQ's worked examples is illustrative, not a
    requirement), and never a hostile string spliced anywhere: `[A-Za-z0-9]+` sequences joined
    by single hyphens, lowercased, `maintainer` as the honest fallback for a name that yields
    nothing."""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    return f"{slug or 'maintainer'}.asc"


# ---------------------------------------------------------------------------------------------
# Reading/writing the genesis commission -- BEFORE the boundary exists (module docstring).
# ---------------------------------------------------------------------------------------------

def _validated_dep_fields(dest: str) -> dict:
    """Reads `<dest>/deployment.json` AND validates the fields this module later splices into
    SQL text (`schema`/`role`/`kern` -- ledger row 1799 finding 5) at THIS boundary, before any
    of them reach a query string. Defense-in-depth, not paranoia: `deployment.json` is
    scaffold-written, not operator-typed, but "trusted here because a trusted process wrote it"
    is exactly the exemption law/adr/0012's 2026-07-18 interpreter-boundary amendment rejects
    ("the input is trusted here does not exempt a site") -- every value is re-checked at the
    splice module's own boundary regardless of provenance, the same discipline
    `probes.pg_connect`'s own schema check already applies to an operator-typed value."""
    path = os.path.join(dest, "deployment.json")
    with open(path, encoding="utf-8") as f:
        dep = json.load(f)
    for _field in ("schema", "role", "kern"):
        _val = dep.get(_field)
        if not isinstance(_val, str) or not probes.valid_identifier(_val):
            raise ValueError(
                f"deployment.json field {_field!r} = {_val!r} is not a valid SQL identifier "
                f"([A-Za-z0-9_]+) -- refusing to splice it into SQL text (law/adr/0012's "
                f"interpreter-boundary rule)"
            )
    return dep


def _psql_json_rows(dep: dict, sql: str, timeout: float = 15.0) -> list[str]:
    argv = ["psql", "-h", dep["host"], "-d", dep["db"], "-t", "-A", "-v", "ON_ERROR_STOP=1",
            "-c", sql]
    r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"psql query failed: {r.stderr.strip()}")
    lines = [ln for ln in r.stdout.strip("\n").splitlines() if ln.strip()]
    # first line echoes the preceding `SET ROLE` statement -- the same documented quirk
    # pickup.tmpl/verify-commission.tmpl's own fetch_commission already carries.
    return lines[1:] if lines else []


def list_commissions(dest: str) -> list[dict]:
    """Every `commission`-kind row currently in force, oldest first -- id/statement/actor only,
    for the operator to designate a genesis row from. Read-only; live under `--dry-run` too (a
    rehearsal that fakes its reads is a lie, per the parent flow spec's own doctrine)."""
    dep = _validated_dep_fields(dest)
    sql = (f"SET ROLE {dep['role']};\n"
           f"SELECT row_to_json(t) FROM (SELECT l.id, l.statement, p.name AS actor "
           f"FROM {dep['schema']}.ledger_current l "
           f"JOIN {dep['kern']}.principal p ON p.id = l.actor "
           f"WHERE l.kind = 'commission' ORDER BY l.id) t;")
    return [json.loads(r) for r in _psql_json_rows(dep, sql)]


def fetch_commission_statement(dest: str, commission_id: int) -> str | None:
    """The EXACT statement bytes for `commission_id`, read the SAME way
    bootstrap/templates/verify-commission.tmpl's own `fetch_commission` does (row_to_json, so
    embedded newlines survive unambiguously) -- see this module's docstring for why this is a
    deliberate byte-fidelity mirror of a file this build may not change, not a re-derivation of
    a fact this module invents its own answer to. None if no such row exists."""
    dep = _validated_dep_fields(dest)
    sql = (f"SET ROLE {dep['role']};\n"
           f"SELECT row_to_json(t) FROM (SELECT l.statement "
           f"FROM {dep['schema']}.ledger_current l "
           f"WHERE l.kind = 'commission' AND l.id = {int(commission_id)}) t;")
    rows = _psql_json_rows(dep, sql)
    if not rows:
        return None
    return json.loads(rows[0])["statement"]


def write_commission(dest: str, statement: str, *,
                      dry_run: bool = False) -> tuple[CommandResult, int | None]:
    """`LED_ACTOR=commissioner <dest>/legacy/led commission "<statement>"` -- FULL mode, this
    world's OWN direct-psql shim (module docstring: the boundary is not up yet at this point in
    the flow). Returns `(result, row_id)`; `row_id` is parsed from the verb's own
    'row <id> written.' convention (shared by led.tmpl and legacy-led.tmpl alike, both driven by
    the same `kernel_write()`/`write_and_report` idiom) -- None under `dry_run` or on failure,
    never fabricated."""
    led = os.path.join(dest, "legacy", "led")
    argv = [led, "commission", statement]
    env = {**os.environ, "LED_ACTOR": "commissioner"}
    res = run_command(argv, env=env, dry_run=dry_run)
    if dry_run or not res.ok:
        return res, None
    return res, runner.parse_row_id(res.output)


# ---------------------------------------------------------------------------------------------
# Keygen -- ONE fixed shape (ed25519, sign-only, no expiry), no quiz (spec §1 item 1).
# ---------------------------------------------------------------------------------------------

@dataclass
class KeygenResult:
    gnupghome: str | None   # None == the operator's own ambient ~/.gnupg (no --homedir at all)
    fingerprint: str | None  # None under dry_run -- nothing was actually generated
    argv: list[str]
    scratch: bool            # True iff THIS module created a throwaway GNUPGHOME to tear down
    ok: bool = True           # runner.run_command's own ok (a SIMULATED success under dry_run,
                               # a real one otherwise) -- the caller's checklist-status source


@dataclass
class ResumeCandidate:
    """A detected partial-ceremony state (ledger row 1799 finding 7), returned by
    `detect_resumable` -- SOME prior act of this ceremony already landed for `name`'s key, so
    unconditionally generating a fresh key would strand the first one (in the operator's own
    keyring, unrecorded and unmentioned) rather than resuming. Every field is a fact this module
    actually observed on disk/in the keyring, never inferred beyond what is checkable."""
    fingerprint: str | None
    key_exported: bool
    keys_path: str
    readme_discharged: bool
    asc_path: str | None
    asc_signed: bool
    secret_key_present: bool


def detect_resumable(dest: str, name: str, gnupghome: str | None,
                      commission_id: int | None = None) -> ResumeCandidate | None:
    """Scans for a partial Signed genesis ceremony for `name`'s key BEFORE any keygen call is
    made -- the resume-after-death check (ledger row 1799 finding 7; WITNESSED in
    seen-red/setup-tui-signed-genesis-resume). Three independent signals, ANY of which means "do
    not blindly generate a fresh key":
      1. `keys/<slug>.asc` already exported for this name (`key_exported`).
      2. `keys/README.md` already shows `KEY COMMITTED` -- discharged by a prior run
         (`readme_discharged`; its recorded fingerprint is parsed out if present).
      3. `commission_id` is known and `.claude/commission-<id>.asc` already exists
         (`asc_signed`) -- signed, but the process may have died before the verify step
         confirmed it.
    Returns `None` if none of the three signals fire (the ordinary fresh-start path) -- never
    fabricates a candidate where nothing partial exists. When a fingerprint IS recorded (from
    the README), `secret_key_present` reports whether a secret key with that EXACT fingerprint
    is actually present in `gnupghome` right now -- the caller uses this to distinguish "safe to
    reuse" from "the recorded fingerprint isn't actually here; refuse rather than pretend.\""""
    filename = key_filename(name)
    keys_path = os.path.join(dest, "keys", filename)
    key_exported = os.path.isfile(keys_path)

    readme_path = os.path.join(dest, "keys", "README.md")
    try:
        with open(readme_path, encoding="utf-8") as f:
            readme_text = f.read()
    except OSError:
        readme_text = ""
    readme_discharged = KEY_COMMITTED_HEADER in readme_text
    fingerprint = None
    if readme_discharged:
        m = re.search(r"fingerprint `([0-9A-Fa-f]+)`", readme_text)
        if m:
            fingerprint = m.group(1)

    asc_path = None
    asc_signed = False
    if commission_id is not None:
        asc_path = os.path.join(dest, ".claude", f"commission-{commission_id}.asc")
        asc_signed = os.path.isfile(asc_path)

    if not (key_exported or readme_discharged or asc_signed):
        return None

    secret_key_present = bool(fingerprint) and fingerprint in _secret_key_fingerprints(gnupghome)
    return ResumeCandidate(
        fingerprint=fingerprint, key_exported=key_exported, keys_path=keys_path,
        readme_discharged=readme_discharged, asc_path=asc_path, asc_signed=asc_signed,
        secret_key_present=secret_key_present,
    )


def _secret_key_fingerprints(gnupghome: str | None) -> list[str]:
    """Every secret-key fingerprint currently in `gnupghome` (`None` == the ambient default
    keyring), oldest-listed first -- the full set, not just the last one (`_list_secret_fpr`
    below is the "just generated, take the newest" convenience; `detect_resumable` needs the
    FULL set to check whether a SPECIFIC recorded fingerprint is actually present)."""
    argv = ["gpg"]
    if gnupghome:
        argv += ["--homedir", gnupghome]
    argv += ["--list-secret-keys", "--with-colons"]
    r = subprocess.run(argv, capture_output=True, text=True)
    return [ln.split(":")[9] for ln in r.stdout.splitlines() if ln.startswith("fpr")]


def _list_secret_fpr(gnupghome: str | None) -> str | None:
    fprs = _secret_key_fingerprints(gnupghome)
    return fprs[-1] if fprs else None


def keygen_scripted(name: str, email: str, *, dry_run: bool = False) -> KeygenResult:
    """The `--scripted` witnessing path (spec §1 item 1): a throwaway GNUPGHOME (tempdir,
    chmod 700 -- `filing/gpg_trust.py`'s own `build_scratch_keyring` shape, mirrored here for a
    KEYGEN rather than an IMPORT, which that function does not perform) + the fixture
    passphrase, fully non-interactive (`--batch --generate-key`). Caller tears the GNUPGHOME
    down via `teardown_scratch` once the ceremony is over."""
    gnupghome = tempfile.mkdtemp(prefix="setup-tui-signed-genesis-scratch-")
    os.chmod(gnupghome, 0o700)
    batch_text = (
        "Key-Type: eddsa\nKey-Curve: ed25519\nKey-Usage: sign\n"
        f"Name-Real: {name}\nName-Email: {email}\nExpire-Date: 0\n"
        f"Passphrase: {FIXTURE_PASSPHRASE}\n%commit\n"
    )
    batch_path = os.path.join(gnupghome, "keygen.batch")
    # The batch file is process-private scratch state -- never inside `dest` (the world this
    # tool's `write_file` choke point governs) -- written directly, same as
    # `filing/gpg_trust.py`'s own scratch-keyring construction.
    with open(batch_path, "w", encoding="utf-8") as f:
        f.write(batch_text)
    argv = ["gpg", "--homedir", gnupghome, "--batch", "--generate-key", batch_path]
    res = run_command(argv, dry_run=dry_run)
    fpr = None if dry_run else _list_secret_fpr(gnupghome)
    return KeygenResult(gnupghome=gnupghome, fingerprint=fpr, argv=argv, scratch=True, ok=res.ok)


def keygen_operator(name: str, email: str, gnupghome: str | None, *,
                     dry_run: bool = False) -> KeygenResult:
    """The operator path (spec §1 item 1): ONE fixed shape, `gpg --quick-generate-key`, no
    quiz -- gpg's OWN interactive passphrase prompt (pinentry), never captured or scripted by
    this tool. `gnupghome` is the operator's own choice; `None` means their own ambient
    `~/.gnupg` (no `--homedir` flag at all, matching the FAQ's own default)."""
    uid = f"{name} <{email}>"
    argv = ["gpg"]
    if gnupghome:
        argv += ["--homedir", gnupghome]
    argv += ["--quick-generate-key", uid, "ed25519", "sign", "0"]
    res = run_command(argv, dry_run=dry_run)
    fpr = None if dry_run else _list_secret_fpr(gnupghome)
    return KeygenResult(gnupghome=gnupghome, fingerprint=fpr, argv=argv, scratch=False,
                         ok=res.ok)


def teardown_scratch(keygen: KeygenResult) -> None:
    """Zero residue (WG1's own bar): removes a scratch GNUPGHOME THIS module created. A no-op
    for the operator path (`scratch=False`) -- the operator's own keyring is NEVER touched by
    this function, or by anything else in this module."""
    if keygen.scratch and keygen.gnupghome:
        shutil.rmtree(keygen.gnupghome, ignore_errors=True)


# ---------------------------------------------------------------------------------------------
# Export + discharge the AWAITING-KEY stub (spec §1 item 2).
# ---------------------------------------------------------------------------------------------

def export_public_key(gnupghome: str | None, fingerprint: str,
                       *, dry_run: bool = False) -> tuple[CommandResult, str]:
    """`gpg [--homedir X] --armor --export <fpr>` -- returns `(result, armored_text)`. Under
    `dry_run` there is no real key to export; `armored_text` is `''` and the caller records a
    WOULD-DO row from the exact argv alone (the same would-be-argv discipline every other
    `--dry-run`-aware act in this package follows)."""
    argv = ["gpg"]
    if gnupghome:
        argv += ["--homedir", gnupghome]
    argv += ["--armor", "--export", fingerprint]
    res = run_command(argv, dry_run=dry_run)
    return res, ("" if dry_run else res.output)


def discharge_keys_readme(dest: str, key_filename_: str, fingerprint: str, name: str,
                           email: str, *, dry_run: bool = False) -> tuple[str, str, bool]:
    """Rewrites `<dest>/keys/README.md`'s `## Current state: AWAITING-KEY` section into
    `## Current state: KEY COMMITTED` -- the real key plus a one-line provenance note (spec §1
    item 2) -- never touching the rest of the templated file
    (`bootstrap/templates/keys-README.md.tmpl`'s own prose stays byte-identical outside this one
    section). Idempotent-replace (ledger row 1790, finding 1 -- ported from
    `durable_decisions.compile_claude_md`'s own marker discipline): the KEY COMMITTED section is
    wrapped in `KEY_COMMITTED_BEGIN`/`KEY_COMMITTED_END` markers, and every run after the FIRST
    real discharge replaces only the marked middle -- a legitimate re-run (key rotation, or
    resume after a death between the README write and verification) can no longer append a
    second, stale-fingerprint section next to the first.

    Three shapes recognized, in order:
      1. Marker pair present (a world discharged by THIS fixed version already) -- replace
         between the markers, the steady-state idempotent path.
      2. `AWAITING-KEY` stub present (never discharged yet) -- replace that section, same
         boundary logic (up to the next `\\n## ` header) this function has always used.
      3. A marker-less `KEY COMMITTED` header present, no markers (migration: a world discharged
         by the already-shipped, pre-fix version of this module) -- replace THAT section in
         place, same boundary logic, rather than appending a second one after it.
      4. None of the above (a stub shape this module does not recognize) -- append rather than
         silently no-op; earlier bytes are still never touched (unchanged fallback).

    Under `dry_run`, the would-be new text is still computed (so the caller can show a real
    content summary) but never written -- `runner.write_file`'s own choke point."""
    path = os.path.join(dest, "keys", "README.md")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    body = (
        f"{KEY_COMMITTED_HEADER}\n\n"
        f"- `{key_filename_}` -- public key for \"{name} <{email}>\", fingerprint "
        f"`{fingerprint}`, committed {stamp} by the Signed genesis ceremony "
        f"(design/FABLE-SETUP-TUI-SIGNED-GENESIS-SPEC.md, tools/setup_tui/signed_genesis.py).\n"
        f"- The **private** key never left the GNUPGHOME it was generated in; its custody is "
        f"the operator's own (user-guide/USER-GPG-TRUST-LAYER-FAQ.md §2 -- print the revocation "
        f"certificate and store it offline).\n"
    )
    section = f"{KEY_COMMITTED_BEGIN}\n{body}{KEY_COMMITTED_END}\n"

    if KEY_COMMITTED_BEGIN in text and KEY_COMMITTED_END in text:
        # Shape 1: steady state -- replace only the marked middle, byte-identical everywhere
        # else (durable_decisions.compile_claude_md's own pattern).
        pre, rest = text.split(KEY_COMMITTED_BEGIN, 1)
        _mid, post = rest.split(KEY_COMMITTED_END, 1)
        new_text = pre + section + post
    else:
        start = text.find(AWAITING_HEADER)
        if start != -1:
            # Shape 2: pre-discharge AWAITING-KEY stub -- unchanged boundary logic from before
            # this fix.
            next_hdr = text.find("\n## ", start + len(AWAITING_HEADER))
            end = next_hdr if next_hdr != -1 else len(text)
            pre, post = text[:start], text[end:]
            new_text = pre + section + post
        else:
            legacy_start = text.find(KEY_COMMITTED_HEADER)
            if legacy_start != -1:
                # Shape 3: migration -- a marker-less KEY COMMITTED section from the
                # already-shipped, pre-fix version. Replace it in place (same boundary as shape
                # 2) rather than appending a second, marker-wrapped section after it.
                next_hdr = text.find("\n## ", legacy_start + len(KEY_COMMITTED_HEADER))
                end = next_hdr if next_hdr != -1 else len(text)
                pre, post = text[:legacy_start], text[end:]
                new_text = pre + section + post
            else:
                # Shape 4: unrecognized -- append rather than silently no-op; earlier bytes are
                # still never touched (unchanged fallback behavior).
                new_text = text + section
    wrote = write_file(path, new_text, dry_run=dry_run, encoding="utf-8")
    return path, new_text, wrote


# ---------------------------------------------------------------------------------------------
# Sign the genesis commission + run the gate (spec §1 items 3-4).
# ---------------------------------------------------------------------------------------------

def sign_statement(gnupghome: str | None, statement: str, asc_path: str, *,
                    scripted: bool, dry_run: bool = False) -> CommandResult:
    """`printf '%s' "$STATEMENT" | gpg --detach-sign --armor -o <asc_path> -` -- the
    byte-fidelity-fixed ceremony (user-guide/USER-GPG-TRUST-LAYER-FAQ.md §5 Step 2,
    bootstrap/new-project.sh's own SIGNED-mode block): `statement` is piped via stdin, never a
    second re-typed/re-read copy (the exact hazard verify-commission.tmpl's own module docstring
    names and fixes). `scripted` selects the non-interactive `--pinentry-mode loopback
    --passphrase` leg (the fixture-passphrase key `keygen_scripted` just made) vs. the
    operator's live pinentry prompt."""
    argv = ["gpg"]
    if gnupghome:
        argv += ["--homedir", gnupghome]
    if scripted:
        argv += ["--batch", "--yes", "--pinentry-mode", "loopback",
                 "--passphrase", FIXTURE_PASSPHRASE]
    argv += ["--detach-sign", "--armor", "-o", asc_path, "-"]
    return run_command(argv, stdin_text=statement, dry_run=dry_run)


def run_verify_commission(dest: str, commission_id: int) -> tuple[CommandResult, dict]:
    """`<dest>/verify-commission --id <id> --json` -- THE gate (spec step 4). Never called under
    `--dry-run` (screens.py's own responsibility: there is no signature to verify that was never
    made -- calling this and pretending its answer would be the exact lie the gate exists to
    prevent). Returns `(result, parsed_json_body)`; `body` is `{}` if the verb's stdout was not
    parseable JSON (never silently treated as a verdict)."""
    verify = os.path.join(dest, "verify-commission")
    res = run_command([verify, "--id", str(commission_id), "--json"])
    try:
        body = json.loads(res.output) if res.output.strip() else {}
    except json.JSONDecodeError:
        body = {}
    return res, body
