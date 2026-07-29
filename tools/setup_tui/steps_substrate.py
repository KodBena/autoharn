#!/usr/bin/env python3
"""tools/setup_tui/steps_substrate.py -- the substrate step's UI-free core, ported from the
pre-rebuild screens.py's `screen_substrate`. The dedicated-db path only ever DISPLAYS a PREPARED
block for the operator to apply by hand on the cluster host -- it queues no Plan entry."""
from __future__ import annotations

from tools.configtree import (ChoiceField, ConfirmField, ElucidationHeading, SectionResult,
                               SectionSpec, TextField, is_field_touched)
from tools.setup_tui import checklist as ck
from tools.setup_tui import feature_facts, idtypes, pghba, probes

_SLUG = "substrate"

SUBSTRATE_CHOICES = (
    ("existing", "existing-db path (zero manual steps)"),
    ("dedicated", "dedicated-db path (generates a confined pg_hba block)"),
)


def _typed_validator(label: str, cls):
    """Live TextField feedback for a `idtypes.PgHost`/`PgDatabase`/`PgRole` field -- delegates to
    the SAME typed home `submit` below constructs through (work item
    setup-tui-bare-types-retrofit, ledger rows 778/789), never a second, ad hoc regex check; only
    translates that type's own `ValueError` into the plain string-or-None a `TextField` validator
    returns, matching `steps_boundary.py`'s own `_validate_sse_poll_interval_secs` idiom."""
    def v(val: str) -> "str | None":
        if not val:
            return None
        try:
            cls.parse(val)
        except ValueError as exc:
            return str(exc)
        return None
    return v


def fields(state: dict) -> tuple:
    return (
        ConfirmField(name="run", label="Configure substrate now?", default=True),
        ChoiceField(name="path", label="Which substrate path?", options=SUBSTRATE_CHOICES,
                    default="existing"),
        TextField(name="host", label="Postgres host", default=state.get("pghost", "192.168.122.1"),
                  required=False, validator=_typed_validator("host", idtypes.PgHost)),
        TextField(name="db_existing", label="Existing database name (existing path)", default="toy",
                  required=False, validator=_typed_validator("database name", idtypes.PgDatabase)),
        TextField(name="db_dedicated", label="New (dedicated) database name", required=False,
                  validator=_typed_validator("database name", idtypes.PgDatabase)),
        TextField(name="role", label="New (dedicated) role name", required=False,
                  validator=_typed_validator("role name", idtypes.PgRole)),
        TextField(name="subnets", label="Subnets to trust (comma-separated CIDR, dedicated path)",
                  default="192.168.122.68/32,192.168.122.1/32", required=False),
    )


def submit(state: dict, answers: dict) -> SectionResult:
    cl = state["_checklist"]
    lines = [feature_facts.facts_block(["substrate_existing", "substrate_dedicated"])]
    if not answers["run"]:
        touched = is_field_touched(state, _SLUG, "run")
        cl.add("substrate", "path chosen", ck.choice_status(touched),
               "operator declined" if touched else "default (never visited/toggled)")
        return SectionResult(ok=True, info_lines=("substrate configuration skipped.",))

    host_raw = answers["host"].strip() or state.get("pghost", "192.168.122.1")
    path = answers["path"]

    # TYPED CONSTRUCTION (work item setup-tui-bare-types-retrofit, ledger rows 778/789,
    # discharging durable row 26's own "if the consumer is in an existing module, the module is
    # rewritten" clause): `host`/`db`/`role` are constructed through `idtypes.PgHost`/`PgDatabase`/
    # `PgRole` -- the ONE typed home per value -- hit whether or not the answer already passed its
    # own field's inline `_typed_validator` (a blank answer skips that validator, the same
    # "only when non-blank" rule `steps_boundary.py`'s own five-value fix documents), rather than
    # a second, ad hoc `probes.valid_*` re-derivation of the same contract. `.value`/`str()` is
    # unwrapped back to a plain scalar immediately below -- state/`pghba`/the prepared psql text
    # all still travel a plain str, byte-identical to before this retrofit.
    try:
        host = str(idtypes.PgHost.parse(host_raw))
    except idtypes.PgHostError as exc:
        return SectionResult(ok=False, errors={"host": str(exc)})
    state = {"substrate_path": path, "pghost": host}

    if path == "existing":
        db_raw = answers["db_existing"].strip() or "toy"
        try:
            db = str(idtypes.PgDatabase.parse(db_raw))
        except idtypes.PgIdentifierError as exc:
            return SectionResult(ok=False, errors={"db_existing": str(exc)})
        ok, detail = probes.pg_reachable(host)
        lines.append(f"  reachability probe: {'GREEN' if ok else 'RED'} -- {detail}")
        cl.add("substrate", f"existing-db {db}@{host} reachable",
               ck.WITNESSED if ok else ck.REFUSED, f"{'GREEN' if ok else 'RED'}: {detail}")
        state["db"] = db
        return SectionResult(ok=True, state_updates=state, info_lines=tuple(lines))

    db_raw, role_raw = answers["db_dedicated"].strip(), answers["role"].strip()
    typed_pg: dict = {}
    for field, cls, raw in (("db_dedicated", idtypes.PgDatabase, db_raw), ("role", idtypes.PgRole, role_raw)):
        try:
            typed_pg[field] = cls.parse(raw)
        except idtypes.PgIdentifierError as exc:
            return SectionResult(ok=False, errors={field: str(exc)})
    db, role = str(typed_pg["db_dedicated"]), str(typed_pg["role"])
    subnet_list = [s.strip() for s in answers["subnets"].split(",") if s.strip()]
    for subnet in subnet_list:
        if not probes.valid_subnet(subnet):
            cl.add("substrate", "dedicated subnets validated", ck.REFUSED, f"'{subnet}' invalid CIDR")
            return SectionResult(ok=False, errors={"subnets": f"'{subnet}' is not a valid CIDR"})

    try:
        block, disclosure = pghba.build_prepared_block(host, db, role, subnet_list, probe_db="toy")
    except pghba.PgHbaReadError as exc:
        cl.add("substrate", "pg_hba block (dedicated)", ck.WITNESSED, f"REFUSED-READ: {exc}")
        return SectionResult(ok=False, errors={"": f"could not read live pg_hba.conf: {exc}"})
    except pghba.PgHbaValidationError as exc:
        cl.add("substrate", "pg_hba block (dedicated)", ck.REFUSED, f"REFUSED: {exc}")
        return SectionResult(ok=False, errors={"": str(exc)})

    lines.append(disclosure)
    lines.append("--- PREPARED: pg_hba.conf block (operator applies, on the cluster host) ---")
    lines.append(block)
    createdb_cmd = f"CREATE ROLE {role} LOGIN; CREATE DATABASE {db} OWNER {role};"
    lines.append("--- PREPARED: createdb/reload block (operator applies, on the cluster host) ---")
    lines.append(f"psql -h {host} -c \"{createdb_cmd}\"")
    lines.append(f"psql -h {host} -c \"SELECT pg_reload_conf();\"")
    cl.add("substrate", "pg_hba block generated", ck.INSTRUCTED,
           f"db={db} role={role} subnets={subnet_list}")
    cl.add("substrate", "createdb/reload block", ck.INSTRUCTED, f"db={db} host={host}")
    state["db"] = db
    state["dedicated_role"] = role
    return SectionResult(ok=True, state_updates=state, info_lines=tuple(lines))


def _headed_facts(*pairs: "tuple[str, str]") -> tuple:
    """`(heading, feature_facts key)` pairs -> ONE elucidation tuple with a REAL sub-heading
    before each fact's own elements (round 7, ledger row 1119, defect D9: "Existing-db path --"/
    "Dedicated-db path --" repeated as a line PREFIX on every row was a flat key-value dump
    faking a hierarchy the reader had to reconstruct by diffing prefixes; a real
    `ElucidationHeading` names each group instead, with the group's own content -- unprefixed --
    following it)."""
    out: list = []
    for heading, key in pairs:
        out.append(ElucidationHeading(heading))
        elements = feature_facts.fact(key).elements()
        if elements is None:
            continue
        out.extend((elements,) if isinstance(elements, str) else elements)
    return tuple(out)


STEP = SectionSpec(
    slug="substrate", title="Substrate", group="Substrate & target", fields=fields, submit=submit,
    description=_headed_facts(("Existing-db path", "substrate_existing"),
                               ("Dedicated-db path", "substrate_dedicated")))
