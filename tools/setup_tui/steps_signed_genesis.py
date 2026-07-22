#!/usr/bin/env python3
"""tools/setup_tui/steps_signed_genesis.py -- the Signed genesis step's UI-free core, ported from
`screen_signed_genesis`. `use_scratch_identity` REPLACES the pre-rebuild's `isinstance(ui,
ScriptedUi)` backend-sniff (that class is deleted with `--scripted`) -- an explicit operator/
config choice instead of an inferred one, honest about what it does (a throwaway GNUPGHOME +
fixture passphrase, never the operator's own keyring), for headless witnessing."""
from __future__ import annotations

import os

from tools.configtree import ConfirmField, SectionResult, SectionSpec, TextField, is_field_touched
from tools.setup_tui import checklist as ck
from tools.setup_tui import content, feature_facts, probes, signed_genesis as sg
from tools.setup_tui.plan import PlanEntry

_SLUG = "signed-genesis"


def fields(state: dict) -> tuple:
    # NO "dest" field here (maintainer ruling 2026-07-22, ADR-0019 single-editable-home): the
    # destination directory is owned by Fork/target -- signed-genesis reads the shared fact
    # straight out of state in `submit` below, never via a second field declaration (a
    # duplicated projection is refused at App construction,
    # `tools.configtree.spec.validate_shared_ownership`).
    return (
        ConfirmField(name="run", label=content.SCREEN_PROMPTS["signed_genesis_ceremony"], default=True),
        TextField(name="statement", label="Founding commission statement (the ask this world "
                  "exists to carry out)", required=False),
        ConfirmField(name="use_scratch_identity", label="Use a throwaway/fixture GPG identity "
                     "(scratch GNUPGHOME, never your own keyring) -- for headless witnessing only"),
        TextField(name="name", label="Key Name-Real", required=False),
        TextField(name="email", label="Key Name-Email", required=False),
        TextField(name="gnupghome", label="GNUPGHOME to use (blank = your default ~/.gnupg, "
                  "operator identity only)", required=False),
    )


def submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    if not answers["run"]:
        touched = is_field_touched(state, _SLUG, "run")
        cl.add("signed-genesis", "ceremony", ck.choice_status(touched),
               "operator declined" if touched else "default (never visited/toggled)")
        return SectionResult(ok=True, info_lines=("signed genesis skipped by operator.",))
    # "dest" is Fork/target's own owned field -- read the shared fact directly (already
    # guaranteed non-empty by `_blocked_needs_dest` below; this section is unreachable otherwise).
    dest = state.get("dest", "").strip()
    dry_run = state.get("dry_run", False)
    lines = [feature_facts.facts_block(["signed_genesis"])]
    if not dest:
        return SectionResult(ok=False, errors={"": "destination (set in Fork/target) required"})

    # ONE disposition, ONE ordering rule (maintainer round 5, ledger row 1115, defect D: a run
    # witnessed BOTH "SKIPPED ... screen 7" and "REFUSED ... not a scaffolded world" for the SAME
    # ceremony item -- two disagreeing records of one fact, plus a sequential-era "screen 7"
    # ghost in a tree UI). Root cause named in the commission: this decision-phase check ran
    # against a PRE-birth destination state even when THIS SAME COMMIT's own plan already
    # contains a birth act that will make it true -- `dest_would_exist` (set by Birth's own
    # `submit`, EARLIER in registry order, the SAME sweep) is therefore consulted FIRST and
    # TRUSTED outright when present, never re-probed against a transitional/pre-act disk state;
    # only when THIS commit does NOT include a same-session birth (an existing, previously-born
    # world is the target) does this fall back to a REAL, live check of what is on disk right
    # now. Exactly one of the two branches below ever runs, exactly one row is ever added under
    # THIS item name for this call.
    if state.get("dest_would_exist"):
        cl.add("signed-genesis", "world has keys/+verify-commission+legacy/led", ck.DRY_SKIPPED,
               f"'{dest}' queued earlier this SAME commit (birth act not yet run) -- trusted, "
               "not re-probed against a pre-birth disk state")
    elif not os.path.isdir(dest):
        cl.add("signed-genesis", "world has keys/+verify-commission+legacy/led", ck.REFUSED,
               f"'{dest}' not a directory")
        return SectionResult(ok=False, errors={"": "destination (set in Fork/target) does not "
                                             "exist -- run a birth first"})
    else:
        missing = [n for n, ok in (
            ("keys/", os.path.isdir(os.path.join(dest, "keys"))),
            ("verify-commission", os.path.isfile(os.path.join(dest, "verify-commission"))),
            ("legacy/led", os.path.isfile(os.path.join(dest, "legacy", "led")))) if not ok]
        if missing:
            cl.add("signed-genesis", "world has keys/+verify-commission+legacy/led", ck.REFUSED,
                   f"missing: {missing} -- not a scaffolded world")
            return SectionResult(ok=False, errors={"": f"missing {missing} -- not a scaffolded world"})
        cl.add("signed-genesis", "world has keys/+verify-commission+legacy/led", ck.WITNESSED, dest)

    gpg_path = probes.which("gpg")
    if not gpg_path:
        cl.add("signed-genesis", "gpg present", ck.REFUSED, "gpg not on PATH")
        return SectionResult(ok=False, errors={"": "'gpg' is not on PATH -- install GnuPG first"})
    cl.add("signed-genesis", "gpg present", ck.WITNESSED, gpg_path)

    plan = state["_plan"]
    statement = answers["statement"].strip()
    if not statement:
        return SectionResult(ok=False, errors={"statement": "required"})
    act, produces = sg.write_commission_act(dest, statement)
    plan.append(PlanEntry(screen="signed-genesis", item="genesis commission written",
                           lesson="the world's founding commission row", act=act, produces=produces))
    commission_id_arg = sg.commission_id_hole()
    lines.append(f"queued: {act.render()}")

    is_scratch = bool(answers["use_scratch_identity"])
    scratch_produces = None
    if is_scratch:
        name = answers["name"].strip() or "AUTOHARN SETUP-TUI FIXTURE KEY -- THROWAWAY"
        email = answers["email"].strip() or "setup-tui-fixture@example.invalid"
        setup_act, scratch_produces = sg.prepare_scratch_gnupghome_act(name, email)
        plan.append(PlanEntry(screen="signed-genesis", item="scratch GNUPGHOME prepared",
                               lesson="throwaway keyring for headless witnessing", act=setup_act,
                               produces=scratch_produces))
        lines.append(f"queued: {setup_act.render()}")
        key_act, key_produces = sg.keygen_scripted_act(sg.gnupghome_hole(), sg.batch_path_hole())
        gnupghome = sg.gnupghome_hole()
    else:
        name, email = answers["name"].strip(), answers["email"].strip()
        if not name or not email:
            return SectionResult(ok=False, errors={"name": "required", "email": "required"})
        gnupghome = answers["gnupghome"].strip() or None
        key_act, key_produces = sg.keygen_operator_act(name, email, gnupghome)
        lines.append("gpg will prompt YOU interactively for a passphrase at commit time.")

    plan.append(PlanEntry(screen="signed-genesis", item="keypair generated",
                           lesson="ONE fixed shape (ed25519, sign-only, no expiry)", act=key_act,
                           produces=key_produces))
    lines.append(f"queued: {key_act.render()}")

    list_act, list_produces = sg.list_secret_key_act(gnupghome)
    plan.append(PlanEntry(screen="signed-genesis", item="fingerprint listed",
                           lesson="the real fingerprint keygen just produced", act=list_act,
                           produces=list_produces))

    export_act, export_produces = sg.export_public_key_act(gnupghome)
    plan.append(PlanEntry(screen="signed-genesis", item="public key exported",
                           lesson="exports the real key to armored text", act=export_act,
                           produces=export_produces))
    filename = sg.key_filename(name)
    keys_write = sg.keys_write_act(dest, filename)
    plan.append(PlanEntry(screen="signed-genesis", item="public key written to keys/",
                           lesson=f"discharges keys/{filename}", act=keys_write))
    discharge = sg.discharge_write_act(dest, filename, name, email)
    plan.append(PlanEntry(screen="signed-genesis", item="keys/README.md AWAITING-KEY discharged",
                           lesson="rewrites keys/README.md's AWAITING-KEY section", act=discharge))

    asc_path = sg.asc_path_arg(dest, commission_id_arg)
    sign_act, sign_produces = sg.sign_statement_act(gnupghome, statement, asc_path, scripted=is_scratch)
    plan.append(PlanEntry(screen="signed-genesis", item="genesis commission signed",
                           lesson="detached signature over the designated commission's statement",
                           act=sign_act, produces=sign_produces))

    if dry_run:
        cl.add("signed-genesis", "ceremony gate (verify-commission)", ck.DRY_SKIPPED,
               "cannot verify a signature that was never made")
    else:
        accept_unverified = bool(state.get("accept_unverified_genesis", False))
        verify_act, verify_produces = sg.verify_commission_act(dest, commission_id_arg,
                                                                 accept_unverified=accept_unverified)
        plan.append(PlanEntry(screen="signed-genesis", item="ceremony gate (verify-commission)",
                               lesson="requires the VERIFIED verdict before recording WITNESSED",
                               act=verify_act, produces=verify_produces))
        lines.append(f"queued: {verify_act.render()}")

    # NOTE: no "dest" here -- it is Fork/target's own owned fact already (ADR-0012 P1: one
    # writer of one truth).
    updates: dict = {}
    if scratch_produces:
        updates["scratch_gnupghome_produces_keys"] = list(
            state.get("scratch_gnupghome_produces_keys", [])) + [scratch_produces]
    return SectionResult(ok=True, state_updates=updates, info_lines=tuple(lines))


def _blocked_needs_dest(state: dict) -> "str | None":
    """The genesis ceremony signs the born world's own commission -- there is nothing to sign
    until Fork/target or Birth has recorded a destination (spec §3 v2's own named example: "the
    genesis gate on rehearsal state" -- this is the sibling edge, on destination)."""
    if state.get("dest"):
        return None
    return "requires: Fork/target or Birth (a destination directory) to be set first"


STEP = SectionSpec(slug="signed-genesis", title="Signed genesis", group="Authority & trust",
                    fields=fields, submit=submit, blocked=_blocked_needs_dest,
                    description=feature_facts.fact("signed_genesis").elements())
