#!/usr/bin/env python3
# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-19T01:39:25Z
#   last-change: 2026-07-19T19:54:08Z
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

from tools.setup_tui import probes
from tools.setup_tui.plan import Arg, CallableAct, CommandAct, Hole, WriteAct
from tools.setup_tui.runner import parse_row_id

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


COMMISSION_PRODUCES = "commission-row"
KEYGEN_PRODUCES = "keygen-ran"
FINGERPRINT_PRODUCES = "fingerprint"
ARMORED_KEY_PRODUCES = "armored-key"


def write_commission_act(dest: str, statement: str) -> tuple[CommandAct, str]:
    """`LED_ACTOR=commissioner <dest>/legacy/led commission "<statement>"` -- FULL mode, this
    world's OWN direct-psql shim (module docstring: the boundary is not up yet at this point in
    the flow), as a plan act. The row id `led` prints on success resolves (at commit) through
    `COMMISSION_PRODUCES`; a later step needing it (the ceremony's own asc-path/verify-id) holds
    a `Hole(of=COMMISSION_PRODUCES, ..., extract=parse_row_id)`, never a value read here."""
    argv = (os.path.join(dest, "legacy", "led"), "commission", statement)
    return CommandAct(argv=argv, extra_env=(("LED_ACTOR", "commissioner"),)), COMMISSION_PRODUCES


def _extract_row_id(output: str) -> str:
    """`Hole.extract` for `write_commission_act`'s real stdout -- the row id as a string (via the
    ONE home for this parse, `runner.parse_row_id`), or the raw output verbatim if unparseable
    (never a fabricated id)."""
    row_id = parse_row_id(output)
    return str(row_id) if row_id is not None else output.strip()


def commission_id_hole() -> Hole:
    """The `Hole` a JUST-WRITTEN genesis commission's row id resolves through -- for an EXISTING,
    already-known commission the caller (screens.py) uses the plain decision-time int/str instead;
    this is only for the "write one now" branch."""
    return Hole(of=COMMISSION_PRODUCES, describe="commission row id", extract=_extract_row_id)


# ---------------------------------------------------------------------------------------------
# Keygen -- ONE fixed shape (ed25519, sign-only, no expiry), no quiz (spec §1 item 1). Every act
# below is a PLAN ACT (Phase 2): built here, appended into THE PLAN by screens.py, executed only
# at the one commit boundary -- gpg is never invoked from this module at decision time.
#
# RESUME-AFTER-DEATH SIMPLIFICATION (Phase 2 design note, ledger row 1799 finding 7's original
# mechanism): the pre-Phase-2 code carried a bespoke `detect_resumable`/`ResumeCandidate` scan for
# a partial ceremony because a screen could die MID-SCREEN under the old progressive-execution
# model, with no other record of how far it got. Under the pure-core model that same "kill mid-way,
# resume cleanly" property is a GENERIC guarantee of `commit_executor.CommitJournal` (WPC4) for
# EVERY plan entry, not just this ceremony's -- a re-invocation against the same destination
# resumes the commit at the first still-PENDING entry, keygen included, with per-act atomicity
# already proven. The bespoke genesis-only archaeology (scanning keys/README.md's own prose,
# re-listing the keyring for a recorded fingerprint) is now a second, narrower resume mechanism
# doing what the journal already does honestly -- so it is retired here, not carried forward
# unused (ADR-0012 P5: remove the root cause, do not let two mechanisms drift). Deliberate
# simplification, named in this build's report, not a silent drop.
# ---------------------------------------------------------------------------------------------

def _parse_fpr_from_colons(colons_output: str) -> str:
    """`Hole.extract` for a `gpg --with-colons --list-secret-keys` real stdout -- the LAST `fpr`
    line's field 10 (gpg's own `--with-colons` format), matching this module's pre-Phase-2
    "just generated, take the newest" convention. Raises (ADR-0002: fail loud, never fabricate) if
    no `fpr` line is present -- keygen produced nothing listable, a real ceremony failure the
    caller's checklist entry must see, not a silently-invented fingerprint."""
    fprs = [ln.split(":")[9] for ln in colons_output.splitlines() if ln.startswith("fpr")]
    if not fprs:
        raise RuntimeError(
            "gpg --list-secret-keys --with-colons produced no 'fpr' line -- keygen did not "
            "leave a listable secret key; nothing to export or sign with"
        )
    return fprs[-1]


def list_secret_key_act(gnupghome: str | None) -> tuple[CommandAct, str]:
    """`gpg [--homedir X] --list-secret-keys --with-colons`, as a plan act run immediately after
    keygen (same commit) -- its REAL stdout is where `FINGERPRINT_PRODUCES` resolves from
    (`_parse_fpr_from_colons`), never a value guessed at decision time (the key does not exist
    until keygen's own act, ordered before this one in the plan, has actually run)."""
    argv = ["gpg"]
    if gnupghome:
        argv += ["--homedir", gnupghome]
    argv += ["--list-secret-keys", "--with-colons"]
    return CommandAct(argv=tuple(argv)), FINGERPRINT_PRODUCES


def fingerprint_hole() -> Hole:
    """The `Hole` any later act's argv holds for the real fingerprint -- resolves against
    `FINGERPRINT_PRODUCES`'s binding (the `list_secret_key_act` entry's real stdout) via
    `_parse_fpr_from_colons`."""
    return Hole(of=FINGERPRINT_PRODUCES, describe="fingerprint", extract=_parse_fpr_from_colons)


SCRATCH_GNUPGHOME_PRODUCES = "scratch-gnupghome"


def _prepare_scratch_gnupghome_raw() -> str:
    """Creates a throwaway GNUPGHOME (tempdir, chmod 700 -- `filing/gpg_trust.py`'s own
    `build_scratch_keyring` shape) for `--scripted` witnessing. NOT gated by the §2.8 purity gate
    -- this is process-private scratch state under `/tmp`, never the destination, the operator's
    keyring, or any ledger -- but it IS a real filesystem effect, so it is called ONLY from
    `prepare_scratch_gnupghome_act`'s own `CallableAct.fn` closure, i.e. only ever at COMMIT time
    (FINDING-2 fix, fresh-context review of b565db1: this used to run at DECISION time under
    `--scripted`, outside the spec's two declared exceptions -- gates/setup_tui_purity_gate.py's
    own EXTRA_EFFECT_EXEMPT names this function explicitly, since the gate cannot itself verify a
    function is only ever invoked from a commit-time closure)."""
    gnupghome = tempfile.mkdtemp(prefix="setup-tui-signed-genesis-scratch-")
    os.chmod(gnupghome, 0o700)
    return gnupghome


def _write_scratch_batch_file_raw(gnupghome: str, name: str, email: str) -> str:
    """Writes gpg's own `--batch --generate-key` batch file INTO the scratch GNUPGHOME
    `_prepare_scratch_gnupghome_raw` just created. Same commit-time-only reasoning and same gate
    exemption as that function -- called only from `prepare_scratch_gnupghome_act`'s closure.
    Returns the batch file's path."""
    batch_text = (
        "Key-Type: eddsa\nKey-Curve: ed25519\nKey-Usage: sign\n"
        f"Name-Real: {name}\nName-Email: {email}\nExpire-Date: 0\n"
        f"Passphrase: {FIXTURE_PASSPHRASE}\n%commit\n"
    )
    batch_path = os.path.join(gnupghome, "keygen.batch")
    with open(batch_path, "w", encoding="utf-8") as f:
        f.write(batch_text)
    return batch_path


def prepare_scratch_gnupghome_act(name: str, email: str) -> tuple[CallableAct, str]:
    """The plan-act builder for the scratch-GNUPGHOME + batch-file setup (FINDING-2 fix): returns
    a `CallableAct` whose `fn` (run only at commit time) creates the scratch GNUPGHOME, writes the
    batch file into it, and returns `(True, gnupghome_path)` -- `gnupghome_path` becomes this
    entry's `produces` binding (`SCRATCH_GNUPGHOME_PRODUCES`), the value every downstream
    `--homedir` argument and the batch-file-path argument resolve against via `Hole`s (see
    `gnupghome_hole`/`batch_path_hole` below) -- never a decision-time string, since the path does
    not exist until this act actually runs."""
    def _fn() -> tuple[bool, str]:
        gnupghome = _prepare_scratch_gnupghome_raw()
        _write_scratch_batch_file_raw(gnupghome, name, email)
        return True, gnupghome
    return CallableAct(fn=_fn, label=f"(scratch GNUPGHOME setup for {name!r})"), \
        SCRATCH_GNUPGHOME_PRODUCES


def gnupghome_hole() -> Hole:
    """The `Hole` a downstream act's `--homedir` argument holds for the scratch GNUPGHOME path --
    resolves against `SCRATCH_GNUPGHOME_PRODUCES`'s binding (`prepare_scratch_gnupghome_act`'s own
    real return value)."""
    return Hole(of=SCRATCH_GNUPGHOME_PRODUCES, describe="scratch gnupghome path",
                extract=lambda gh: gh)


def batch_path_hole() -> Hole:
    """The `Hole` `keygen_scripted_act`'s own batch-file argument holds -- the scratch GNUPGHOME
    path plus the fixed `keygen.batch` filename `_write_scratch_batch_file_raw` always uses."""
    return Hole(of=SCRATCH_GNUPGHOME_PRODUCES, describe="scratch batch file path",
                extract=lambda gh: os.path.join(gh, "keygen.batch"))


def keygen_scripted_act(gnupghome: str, batch_path: str) -> tuple[CommandAct, str]:
    """The `--scripted` witnessing keygen (spec §1 item 1), as a plan act: `gpg --homedir
    <gnupghome> --batch --generate-key <batch_path>`, fully non-interactive."""
    argv = ("gpg", "--homedir", gnupghome, "--batch", "--generate-key", batch_path)
    return CommandAct(argv=argv), KEYGEN_PRODUCES


def keygen_operator_act(name: str, email: str, gnupghome: str | None) -> tuple[CommandAct, str]:
    """The operator path (spec §1 item 1), as a plan act: ONE fixed shape, `gpg
    --quick-generate-key`, no quiz -- gpg's OWN interactive passphrase prompt (pinentry) at
    COMMIT time, never captured or scripted by this tool. `gnupghome` is the operator's own
    choice; `None` means their own ambient `~/.gnupg` (no `--homedir` flag at all)."""
    uid = f"{name} <{email}>"
    argv = ["gpg"]
    if gnupghome:
        argv += ["--homedir", gnupghome]
    argv += ["--quick-generate-key", uid, "ed25519", "sign", "0"]
    return CommandAct(argv=tuple(argv)), KEYGEN_PRODUCES


def teardown_scratch(gnupghome: str | None) -> None:
    """Zero residue (WG1's own bar): removes a scratch GNUPGHOME `prepare_scratch_gnupghome`
    created. A no-op for `None` (the operator path never has one) -- the operator's own keyring is
    NEVER touched by this function, or by anything else in this module."""
    if gnupghome:
        shutil.rmtree(gnupghome, ignore_errors=True)


# ---------------------------------------------------------------------------------------------
# Export + discharge the AWAITING-KEY stub (spec §1 item 2).
# ---------------------------------------------------------------------------------------------

def export_public_key_act(gnupghome: str | None) -> tuple[CommandAct, str]:
    """`gpg [--homedir X] --armor --export <fpr>` -- `<fpr>` is `fingerprint_hole()`, resolved at
    commit against the REAL keygen just above. Its own real stdout (the armored key text) IS
    `ARMORED_KEY_PRODUCES`'s binding -- the write below reads it back via a plain identity
    `Hole`, never a value captured here."""
    argv: tuple[Arg, ...] = (("gpg",) if not gnupghome else ("gpg", "--homedir", gnupghome))
    argv = argv + ("--armor", "--export", fingerprint_hole())
    return CommandAct(argv=argv), ARMORED_KEY_PRODUCES


def keys_write_act(dest: str, filename: str) -> WriteAct:
    """`<dest>/keys/<filename>` <- the exported armored key, as a plan act -- content is a plain
    identity `Hole` on `ARMORED_KEY_PRODUCES` (the export act's own real stdout)."""
    return WriteAct(
        path=os.path.join(dest, "keys", filename),
        content=Hole(of=ARMORED_KEY_PRODUCES, describe="armored public key",
                     extract=lambda armored: armored),
    )


def _compute_discharge_text(dest: str, key_filename_: str, fingerprint: str, name: str,
                             email: str) -> str:
    """The pure text-computation half of the pre-Phase-2 `discharge_keys_readme` (unchanged
    marker/shape logic; see the four recognized shapes in the comments below) -- reads
    `<dest>/keys/README.md`'s CURRENT bytes (a live read, done at COMMIT time by the closure this
    function backs, since birth's own write of that file has by then actually happened -- plan
    entries execute strictly in order) and returns the new full text. Never writes; the caller
    (`discharge_write_act`'s `Hole`) is the one WriteAct that does."""
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
        # Shape 1: steady state -- replace only the marked middle, byte-identical everywhere else.
        pre, rest = text.split(KEY_COMMITTED_BEGIN, 1)
        _mid, post = rest.split(KEY_COMMITTED_END, 1)
        return pre + section + post
    start = text.find(AWAITING_HEADER)
    if start != -1:
        # Shape 2: pre-discharge AWAITING-KEY stub -- boundary is the next "\n## " header.
        next_hdr = text.find("\n## ", start + len(AWAITING_HEADER))
        end = next_hdr if next_hdr != -1 else len(text)
        return text[:start] + section + text[end:]
    legacy_start = text.find(KEY_COMMITTED_HEADER)
    if legacy_start != -1:
        # Shape 3: migration -- a marker-less KEY COMMITTED section from an older world.
        next_hdr = text.find("\n## ", legacy_start + len(KEY_COMMITTED_HEADER))
        end = next_hdr if next_hdr != -1 else len(text)
        return text[:legacy_start] + section + text[end:]
    # Shape 4: unrecognized -- append rather than silently no-op.
    return text + section


def discharge_write_act(dest: str, key_filename_: str, name: str, email: str) -> WriteAct:
    """`<dest>/keys/README.md`'s AWAITING-KEY discharge (spec §1 item 2), as a plan act. `content`
    is a `Hole` on `FINGERPRINT_PRODUCES` whose `extract` does MORE than the ordinary "pull a
    value out of real stdout" -- it calls `_compute_discharge_text`, which does its own live read
    of the CURRENT `keys/README.md` at the moment this act runs (necessarily after birth's own
    write of that file, by plan order). This is the same "resolved at commit, not at decision"
    discipline every Hole here follows; it is legitimate BECAUSE `of` genuinely names the real
    entry (`list_secret_key_act`) this act depends on -- the fingerprint really is what makes this
    write correct to perform."""
    return WriteAct(
        path=os.path.join(dest, "keys", "README.md"),
        content=Hole(
            of=FINGERPRINT_PRODUCES, describe="keys/README.md new content (KEY COMMITTED)",
            extract=lambda fpr: _compute_discharge_text(dest, key_filename_, fpr, name, email),
        ),
    )


# ---------------------------------------------------------------------------------------------
# Sign the genesis commission + run the gate (spec §1 items 3-4).
# ---------------------------------------------------------------------------------------------

def asc_path_arg(dest: str, commission_id_arg: Arg) -> Arg:
    """The exact `.claude/commission-<id>.asc` path this ceremony signs into, as an `Arg` of the
    SAME kind as `commission_id_arg` -- a plain string if the genesis commission was an EXISTING,
    decision-time-known row; a `Hole` (folding the path-building into ONE extract, since `plan.py`'s
    `Arg` is `str | Hole`, not recursive) if it was just written this same commit and its row id is
    itself a `Hole`."""
    if isinstance(commission_id_arg, Hole):
        inner = commission_id_arg
        return Hole(of=inner.of, describe="asc-path",
                    extract=lambda output: os.path.join(
                        dest, ".claude", f"commission-{inner.extract(output)}.asc"))
    return os.path.join(dest, ".claude", f"commission-{commission_id_arg}.asc")


def sign_statement_act(gnupghome: str | None, statement: str, asc_path: Arg, *,
                        scripted: bool) -> tuple[CommandAct, str]:
    """`printf '%s' "$STATEMENT" | gpg --detach-sign --armor -o <asc_path> -` -- the
    byte-fidelity-fixed ceremony (user-guide/USER-GPG-TRUST-LAYER-FAQ.md §5 Step 2), as a plan
    act. `statement` is a plain string known at decision time either way (an existing commission's
    text, read live, or the operator's own freshly-typed text) -- it is what gets SIGNED, piped via
    `stdin_text`, never a second re-typed/re-read copy. `scripted` selects the non-interactive
    `--pinentry-mode loopback --passphrase` leg vs. the operator's live pinentry prompt at commit
    time."""
    argv: list[Arg] = ["gpg"]
    if gnupghome:
        argv += ["--homedir", gnupghome]
    if scripted:
        argv += ["--batch", "--yes", "--pinentry-mode", "loopback", "--passphrase",
                 FIXTURE_PASSPHRASE]
    argv += ["--detach-sign", "--armor", "-o", asc_path, "-"]
    return CommandAct(argv=tuple(argv), stdin_text=statement), "signed-asc"


def verify_commission_act(dest: str, commission_id_arg: Arg) -> tuple[CommandAct, str]:
    """`<dest>/verify-commission --id <id> --json` -- THE gate (spec step 4), as a plan act
    ordered LAST in the ceremony (after signing) so it verifies the signature this SAME commit
    just made. Never appended to the plan under `--dry-run` at all (screens.py's own
    responsibility -- there is no signature to verify that was never made; the WOULD-DO table
    shows a `DRY-SKIPPED` row instead, never a faked argv for an act that will never run). The
    real verdict is parsed from this entry's own real stdout by the caller's `on_result` callback
    (screens.py), not here -- `verify-commission` itself exits 0 whether or not the verdict is
    VERIFIED (module docstring's own "TWO VERBS" note), so the commit executor's own `ok` (exit
    code) is not the signal; the JSON body's `verdict` field is, and that parse is a decision the
    CHECKLIST makes, which is screens.py's job."""
    verify = os.path.join(dest, "verify-commission")
    return CommandAct(argv=(verify, "--id", commission_id_arg, "--json")), "verify-body"


def parse_verify_body(output: str) -> dict:
    """The SAME JSON-or-empty-dict parse the pre-Phase-2 `run_verify_commission` used --
    `output` is a real `verify-commission --json` stdout; `{}` if unparseable, never treated as a
    verdict."""
    try:
        return json.loads(output) if output.strip() else {}
    except json.JSONDecodeError:
        return {}
