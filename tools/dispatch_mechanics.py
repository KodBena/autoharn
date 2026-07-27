#!/usr/bin/env python3
"""dispatch_mechanics -- the scripted `./autoharn dispatch` verb (design/
FABLE-DISPATCH-MECHANICS-SPEC.md §3, ledger rows 1463/1467/1468/1471). Two subcommands:

    dispatch mint <name> <commission-row-id>[,<commission-row-id>...] [--depth N]
                  [--purpose <why>] [--independent-verification] [--deployment <path>]
    dispatch close <name> [<reason...>] [--deployment <path>]

TARGET SCOPING (fresh-context review CRITICAL, ledger rows 1525/1526 -- the live-deployment
incident): this verb REFUSES to run unless its target deployment record is EXPLICIT -- either
`--deployment <path/to/deployment.json>` on the command line or the `LEDGER_DEPLOYMENT`
environment variable. There is NO default: the previous behavior (fall back to the
deployment.json beside this script's own repo) is exactly what let a scratch-world exercise of
`mint` land four rows on the live deployment (real-ledger rows 1521-1524, standing as
documented history). An authority-bearing verb never guesses its target; the operator names
it, every invocation, and the refusal text teaches both spellings.

`mint` performs the spec's own three-step dispatch act, in order: (1) mints the delegate
principal via the existing led registration machinery (`POST /write/registration`, the SAME
surface `./led register-principal` uses -- no new registration mechanism); (2) writes the
`dispatched-by` edge, carrying the commission row ids (as `refs`) and the delegation caveats
kernel/lineage/s64-principal-stamps-delegation-conditions.sql defines (`delegation_redelegate_
depth`, `delegation_purpose`) -- via `POST /write/ledger` directly (kind=
principal_relation_asserted), because NO existing CLI surface exposes s64's five delegation-
condition columns yet (`led principal relate` predates s64 and has no flags for them; s64's own
header states plainly that hooks/dispatch-mechanics were explicitly out of ITS scope) -- this is
that missing surface, built here, not a raw-SQL workaround (still POSTs through the served
boundary, still through kernel.ledger_write, still s43-gated); (3) emits the stamp material for
the child session's own environment -- `export AUTOHARN_MINTED_PRINCIPAL=<id>` and `export
LED_ACTOR=<name>` -- ready to paste into (or `eval`'d by) a dispatch preamble.

DEFAULTS (ledger row 1471 sub-item 4c, binding at this build): `--depth` defaults to 0
(no-redelegate ALWAYS on a leaf brief) -- depth-N is an explicit, named opt-in at this verb's own
surface, never a default. `--independent-verification` sets `delegation_purpose =
'independent-verification'` (the s64 carve-out, row 1420) -- the delegate's dispatch is EXEMPT
BY TYPE from the no-redelegate/depth conjunct for its OWN further dispatch of an independent
verifier, while every other conjunct (writer-chains-to-genesis, scope, expiry, countersign)
stays fully in force (kernel/lineage/s64-principal-stamps-delegation-conditions.sql, "WHY, THE
THREE MECHANISMS", mechanism 3).

RESIDUE SWEEP (spec §3: "the next mint-verb run reports unclosed principals loudly"): before
minting, `mint` scans this dispatcher's own in-force `dispatched-by` edges for a delegate whose
standing is still 'active' (never suspended/revoked) -- i.e. never closed by a prior `dispatch
close` -- and prints each one, loudly, to stderr. This is INFORMATIONAL ONLY (never blocks the
new mint): SessionEnd-triggered automatic retirement is explicitly parked (spec §3, "the
eventual automatic trigger is a SessionEnd hook ... until then the orchestrator's close verb is
the mechanism").

`close` retires the named principal via the EXISTING standing-lifecycle machinery
(kernel/lineage/s45-standing-lifecycle.sql, `POST /write/ledger` kind=principal_suspended -- the
SAME typed standing event `led principal suspend`/`tools/dispatch_principal.py`'s own docstring
both already name as the retirement mechanism, never a new one minted here).

DISPATCHER IDENTITY: both subcommands resolve the ACTING (dispatching) principal from `LED_ACTOR`
(the SAME env var `led` itself reads) -- required and REFUSED, loudly, if unset or unregistered
(a `dispatched-by` edge must be authored BY the dispatcher, s62's own remedy: "the delegator
authors the edge, never the delegate" -- there is no anonymous-dispatcher default here, unlike
`led`'s own generic write path, because this act is authority-bearing by construction).

NO KERNEL/HOOKS CHANGE: this tool writes ordinary ledger rows through the existing served
boundary and existing kernel functions; it mints no new mechanism, installs no hook (the
SessionEnd retirement hook stays parked, per the spec's own §4), and never touches raw SQL.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import is top-of-file.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent  # repo root (tools/ is one level under it)

sys.path.insert(0, str(HERE / "serving"))
sys.path.insert(0, str(HERE / "filing"))
import boundary_cli_client as bcc  # noqa: E402
import ensure_running as er  # noqa: E402

PROG = "dispatch"


def _resolve_deployment_path(explicit: str | None) -> Path:
    """The verb's target-scoping gate (module docstring, "TARGET SCOPING") -- an explicit
    `--deployment` flag wins, then the `LEDGER_DEPLOYMENT` environment variable; NO other
    source, and in particular never this script's own repo location (real-ledger rows
    1521-1524 are the witnessed cost of that default). Refuses with teaching text, before any
    config read or network touch, when neither is present."""
    if explicit:
        return Path(explicit)
    env = os.environ.get("LEDGER_DEPLOYMENT", "")
    if env:
        return Path(env)
    print(f"{PROG}: REFUSED -- no target deployment named. This verb writes authority-bearing "
          f"rows (principal registrations, dispatched-by edges, suspensions) and will not "
          f"guess which world receives them: name the target explicitly, either\n"
          f"    {PROG} ... --deployment <path/to/deployment.json>\n"
          f"or\n"
          f"    LEDGER_DEPLOYMENT=<path/to/deployment.json> {PROG} ...\n"
          f"(The former default -- the deployment.json beside this script's own repo -- is "
          f"exactly how a scratch-world exercise once landed rows on the live deployment; "
          f"ledger rows 1525/1526.)", file=sys.stderr)
    sys.exit(2)


def _load_config(deployment_path: Path) -> bcc.ServedConfig:
    """Mirrors `bootstrap/templates/led.tmpl`'s own `_load_config` (ADR-0012 P1: the same
    resolve-then-handshake-then-ensure-running-once shape, not a second copy of its reasoning)."""
    try:
        cfg = bcc.load_served_config(deployment_path)
    except bcc.BoundaryClientError as e:
        print(f"{PROG}: {e}", file=sys.stderr)
        sys.exit(4)
    try:
        bcc.check_protocol_version(cfg.base, cfg.record.boundary_url)
    except bcc.BoundaryUnreachable:
        er.ensure_running_or_leave_unreachable(deployment_path, PROG)
        bcc.check_protocol_version(cfg.base, cfg.record.boundary_url)
    return cfg


def _principals_by_name(cfg: bcc.ServedConfig) -> dict[str, int]:
    rows = bcc.get_all_rows(cfg.base, "/standing/principals", cursor="after_id")
    return {r["name"]: r["id"] for r in rows}


def _resolve_dispatcher(cfg: bcc.ServedConfig, by_name: dict[str, int]) -> int:
    """The acting (dispatching) principal -- LED_ACTOR, required here (unlike `led`'s own
    generic write path, where an unset LED_ACTOR quietly means "let the kernel's own
    declared-default resolution apply"): a `dispatched-by` edge is authority-bearing by
    construction and must be authored BY a real, named dispatcher (s62's remedy)."""
    name = os.environ.get("LED_ACTOR", "")
    if not name:
        print(f"{PROG}: REFUSED -- LED_ACTOR must name the DISPATCHING principal (the "
              f"orchestrator's own registered identity) -- a dispatched-by edge is "
              f"authority-bearing and must be authored BY a real principal, never anonymous.",
              file=sys.stderr)
        sys.exit(1)
    pid = by_name.get(name)
    if pid is None:
        print(f"{PROG}: REFUSED -- LED_ACTOR={name!r} is not a registered principal. Register "
              f"it first: ./led register-principal {name} <human|model|tool>", file=sys.stderr)
        sys.exit(1)
    return pid


def _principal_standing(cfg: bcc.ServedConfig, pid: int) -> str:
    """Reads this principal's current standing off `GET /views/principal_standing_current` --
    the SAME kernel-derived view `led`'s own `/standing/principals` route (`_principals_by_name`
    above) is built from, at a finer per-row grain (status, not just name/id)."""
    for r in bcc.get_all_rows(cfg.base, "/standing/principals", cursor="after_id"):
        if r.get("id") == pid:
            return str(r.get("standing", "unknown"))
    return "unknown"


def _sweep_unclosed(cfg: bcc.ServedConfig, dispatcher_id: int, by_id: dict[int, str]) -> None:
    """spec §3: "the next mint-verb run reports unclosed principals loudly." Scans this
    dispatcher's own in-force `dispatched-by` edges (principal_relation_asserted,
    principal_binding_active=true, principal_object=dispatcher_id, principal_relation=
    'dispatched-by') for a delegate whose standing is not 'active' -- wait, the INTERESTING
    residue is the OPPOSITE: a delegate whose standing IS STILL 'active' (never suspended via
    `dispatch close`) is the one that was never retired. INFORMATIONAL ONLY -- never blocks."""
    rows = bcc.get_all_rows(cfg.base, "/rows/current", cursor="after_id")
    unclosed: list[str] = []
    for r in rows:
        if (r.get("kind") == "principal_relation_asserted"
                and r.get("principal_relation") == "dispatched-by"
                and r.get("principal_binding_active") is True
                and r.get("principal_object") == dispatcher_id):
            subj = r.get("principal_subject")
            name = by_id.get(subj, f"id={subj}")
            standing = _principal_standing(cfg, subj) if subj is not None else "unknown"
            if standing == "active":
                unclosed.append(name)
    if unclosed:
        print(f"{PROG}: NOTE -- {len(unclosed)} previously dispatched principal(s) still show "
              f"'active' standing (never retired by `dispatch close`): {sorted(set(unclosed))}. "
              f"This is informational only (spec §3's own residue-sweep, not a refusal) -- close "
              f"them with `./autoharn dispatch close <name>` when their session is genuinely "
              f"done.", file=sys.stderr)


def cmd_mint(argv: list[str]) -> int:
    positional: list[str] = []
    depth = 0
    purpose: str | None = None
    independent_verification = False
    deployment_flag: str | None = None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--deployment":
            if i + 1 >= len(argv):
                print(f"{PROG} mint: --deployment requires a path", file=sys.stderr)
                return 2
            deployment_flag = argv[i + 1]
            i += 2
        elif a == "--depth":
            if i + 1 >= len(argv):
                print(f"{PROG} mint: --depth requires a value", file=sys.stderr)
                return 2
            try:
                depth = int(argv[i + 1])
            except ValueError:
                print(f"{PROG} mint: --depth value {argv[i + 1]!r} is not an integer", file=sys.stderr)
                return 2
            if depth < 0:
                print(f"{PROG} mint: --depth must be >= 0 (0 = no-redelegate, the default)", file=sys.stderr)
                return 2
            i += 2
        elif a == "--purpose":
            if i + 1 >= len(argv):
                print(f"{PROG} mint: --purpose requires a value", file=sys.stderr)
                return 2
            purpose = argv[i + 1]
            i += 2
        elif a == "--independent-verification":
            independent_verification = True
            i += 1
        else:
            positional.append(a)
            i += 1
    if len(positional) != 2:
        print(f"usage: {PROG} mint <name> <commission-row-id>[,<commission-row-id>...] "
              f"[--depth N] [--purpose <why>] [--independent-verification] "
              f"[--deployment <path>]", file=sys.stderr)
        return 2
    name, commission_ids_raw = positional
    try:
        commission_ids = [int(x) for x in commission_ids_raw.split(",") if x]
    except ValueError:
        print(f"{PROG} mint: REFUSED -- commission row ids must be a comma-separated list of "
              f"integers, got {commission_ids_raw!r}", file=sys.stderr)
        return 2
    if not commission_ids:
        print(f"{PROG} mint: REFUSED -- at least one commission row id is required (spec §2.4, "
              f"commission re-hydration -- a dispatch edge with no commission to re-hydrate "
              f"against is exactly the stale-copy-coherence hazard this spec closes).", file=sys.stderr)
        return 2

    deployment_path = _resolve_deployment_path(deployment_flag)
    cfg = _load_config(deployment_path)
    by_name = _principals_by_name(cfg)
    by_id = {v: k for k, v in by_name.items()}
    dispatcher_id = _resolve_dispatcher(cfg, by_name)

    _sweep_unclosed(cfg, dispatcher_id, by_id)

    if name in by_name:
        print(f"{PROG} mint: REFUSED -- '{name}' is already a registered principal (id "
              f"{by_name[name]}) -- pick a distinct name for this dispatch (e.g. "
              f"builder-<work-item-slug>-<n>).", file=sys.stderr)
        return 1

    # Step 1: mint the delegate principal (the SAME registration surface `led register-principal`
    # uses -- s40's own registration machinery, no second mechanism).
    reg_payload = {"name": name, "agent_class": "subagent",
                   "purpose": purpose or f"dispatched delegate for commission row(s) {commission_ids}",
                   "actor": dispatcher_id}
    rc = bcc.write_and_report(cfg.base, "registration", reg_payload)
    if rc != 0:
        return rc
    by_name = _principals_by_name(cfg)  # re-read: the new principal's id
    delegate_id = by_name.get(name)
    if delegate_id is None:
        print(f"{PROG} mint: REFUSED -- registration reported accepted but '{name}' is not yet "
              f"visible on GET /standing/principals (a read-after-write anomaly) -- do not "
              f"proceed; investigate before retrying.", file=sys.stderr)
        return 1

    # Step 2: write the dispatched-by edge, carrying the commission row ids (as `refs`) and the
    # s64 delegation caveats. No existing CLI surface exposes these five columns (see module
    # docstring) -- POSTs kind=principal_relation_asserted directly through /write/ledger, the
    # SAME generic surface `led`'s own `_write_principal` helper already uses for every one of
    # the 13 `led principal *` sub-verbs.
    edge_payload: dict = {
        "kind": "principal_relation_asserted",
        "statement": f"principal '{name}' dispatched-by principal (dispatcher id {dispatcher_id}) "
                     f"-- commission row(s) {commission_ids}",
        "principal_subject": delegate_id,
        "principal_relation": "dispatched-by",
        "principal_object": dispatcher_id,
        "principal_binding_active": True,
        "delegation_redelegate_depth": depth,
        "actor": dispatcher_id,
        "refs": ",".join(str(x) for x in commission_ids),
    }
    if independent_verification:
        edge_payload["delegation_purpose"] = "independent-verification"
    rc = bcc.write_and_report(cfg.base, "ledger", edge_payload)
    if rc != 0:
        print(f"{PROG} mint: the delegate principal '{name}' (id {delegate_id}) IS now "
              f"registered, but its dispatched-by edge was REFUSED (above) -- it currently has "
              f"NO recorded dispatch authority. Do not emit its stamp material to a child "
              f"session until this is resolved.", file=sys.stderr)
        return rc

    # Step 3: emit the stamp material for the child session's environment (spec §3, verbatim).
    print(f"# dispatch-mechanics mint: '{name}' (principal id {delegate_id}), "
          f"depth={depth}, commission row(s) {commission_ids}")
    print(f"export AUTOHARN_MINTED_PRINCIPAL={delegate_id}")
    print(f"export LED_ACTOR={name}")
    return 0


def cmd_close(argv: list[str]) -> int:
    deployment_flag: str | None = None
    rest: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--deployment":
            if i + 1 >= len(argv):
                print(f"{PROG} close: --deployment requires a path", file=sys.stderr)
                return 2
            deployment_flag = argv[i + 1]
            i += 2
        else:
            rest.append(argv[i])
            i += 1
    if not rest:
        print(f"usage: {PROG} close <name> [<reason...>] [--deployment <path>]", file=sys.stderr)
        return 2
    name = rest[0]
    reason = " ".join(rest[1:]) or "dispatch session closed (dispatch-mechanics close verb)"
    deployment_path = _resolve_deployment_path(deployment_flag)
    cfg = _load_config(deployment_path)
    by_name = _principals_by_name(cfg)
    pid = by_name.get(name)
    if pid is None:
        print(f"{PROG} close: REFUSED -- '{name}' is not a registered principal.", file=sys.stderr)
        return 1
    standing = _principal_standing(cfg, pid)
    if standing != "active":
        print(f"{PROG} close: '{name}' (id {pid}) already shows standing {standing!r} -- "
              f"nothing to do.", file=sys.stderr)
        return 0
    dispatcher_id = _resolve_dispatcher(cfg, by_name)
    payload = {
        "kind": "principal_suspended",
        "statement": f"principal '{name}' suspended -- standing withdrawn: {reason}",
        "principal_subject": pid,
        # kernel/lineage/s45-standing-lifecycle.sql widens principal_binding_active_kind_shape
        # to REQUIRE this field NOT NULL on principal_suspended (mandatory-iff-active-kind,
        # matching `led principal suspend`'s own StandingLifecyclePayload -- active=True on an
        # s45 world). Omitting it here would violate that CHECK -- witnessed live during this
        # build's own scratch witness run, fixed here rather than silently left broken.
        "principal_binding_active": True,
        "actor": dispatcher_id,
    }
    return bcc.write_and_report(cfg.base, "ledger", payload)


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("--help", "-h", "help"):
        print(__doc__)
        return 0
    sub, rest = argv[0], argv[1:]
    try:
        if sub == "mint":
            return cmd_mint(rest)
        if sub == "close":
            return cmd_close(rest)
        print(f"{PROG}: unrecognized subcommand {sub!r} (usage: {PROG} mint|close ...)", file=sys.stderr)
        return 2
    except bcc.ProtocolVersionMismatch as e:
        return bcc.report_protocol_mismatch(PROG, e)
    except (bcc.BoundaryRefusal, bcc.BoundaryUnreachable, bcc.BoundaryClientError) as e:
        return bcc.report_boundary_exception(PROG, e)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
