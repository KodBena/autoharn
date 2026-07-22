#!/usr/bin/env python3
"""boundary_cli_client -- the ONE home for "how a rebased operator-verb shim talks to the
boundary service" (design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-SPEC.md §5; design/
FABLE-BOUNDARY-READ-SURFACE-SPEC.md, ledger decision rows 1631/1652). Every rebased shim
(`led`, `pickup`, `asof-export`, `distance-to-clean`) imports THIS module rather than each
re-deriving its own urllib boilerplate, pagination walk, or exit-code convention (ADR-0012 P1).

TRANSPORT: stdlib `urllib.request` only -- this project has no HTTP client dependency anywhere
else (`serving/`'s own witness fixtures already use the identical `urllib`-only convention), and
a rebased CLI shim is exactly as system-scoped as the boundary service itself; introducing a
third-party HTTP library here would be a second transport for the same project (the same
reasoning `serving/boundary_service.py`'s own module docstring gives for staying on `psql`
rather than `psycopg`).

DEPLOYMENT RESOLUTION: `deployment.json` gains two new OPTIONAL keys (spec §5): `boundary_url`
(the served boundary's own base URL, no trailing slash, no `/d/{deployment}` segment) and
`boundary_deployment` (the `/d/{name}` path segment this project answers under on the served
side -- deliberately distinct from `deployment.json`'s pre-existing `name` field, see
`filing/deployment_record.py`'s own comment for why). `load_served_config` below is the ONE
place a rebased shim resolves both and refuses loudly, by name, when either is absent -- spec
§5's own words: "two new keys, refused-if-absent by the new shims."

EXIT-CODE CONVENTION (spec §5: "a boundary refusal must never be dressed as a kernel refusal",
A4's exit-code-fidelity ruling extended to this shim layer). Four codes, named ONCE:
  0  KERNEL ACCEPTED   -- the s43 write_verdict's own 'accepted' disposition. Byte-identical to
                          the legacy direct-psql `led`'s own `kernel_write()` exit (0).
  1  KERNEL REFUSED    -- the s43 write_verdict's own 'refused' disposition -- a first-class,
                          journaled domain result, not a transport error. Byte-identical to the
                          legacy `led`'s own exit (1) for exactly this case (see
                          bootstrap/templates/led.tmpl's own `kernel_write()`).
  3  BOUNDARY REFUSED   -- a typed HTTP 4xx/408/413/422/429/503/409 shape FROM THE BOUNDARY
                          ITSELF (serving/boundary_service.py's own typed refusals:
                          payload_too_large/body_read_timeout/server_saturated/
                          deployment_saturated/unknown_deployment/unknown_view/
                          capability_absent/a bare 422 shape check) -- there was NO kernel
                          write_verdict at all for this call; dressing it as exit 1 would let a
                          boundary-level refusal masquerade as a kernel one (the class this
                          exit code exists to foreclose, spec §5 verbatim).
  4  BOUNDARY UNREACHABLE -- the HTTP request to the boundary itself failed (connection refused,
                          DNS failure, timeout) -- this shim never had a response to classify.
                          Distinct from 3 (which DID get a response, just a refusing one).
Never exit 2 -- reserved, unused here, precisely because the LEGACY direct-psql tools propagate
psql's OWN raw exit codes (which include 2 for a connection-level psql failure); keeping this
shim's own vocabulary disjoint from that legacy range means a caller inspecting an exit code
alone can never confuse "the legacy psql tool's connection failed" with "the served shim's own
boundary call was refused" even if both tools are invoked interchangeably during the ./legacy/
transition.

Lazy imports are banned (CLAUDE.md, 2026-07-02): every import is top-of-file.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "filing"))
import deployment_record  # noqa: E402


class BoundaryClientError(Exception):
    """Refused before any HTTP call was even attempted -- a malformed/incomplete deployment.json
    (the two new keys, spec §5), or an argument this client itself refuses to forward (never a
    boundary or kernel response; those are `BoundaryRefusal`/`BoundaryUnreachable` below)."""


class BoundaryUnreachable(Exception):
    """Exit code 4 (see module docstring): the HTTP request to the boundary itself failed --
    connection refused, DNS failure, timeout. `detail` carries the underlying `OSError`/
    `urllib.error.URLError` text (never SQL/role/schema/stack -- there was no boundary response
    to leak one from in the first place)."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class BoundaryRefusal(Exception):
    """Exit code 3 (see module docstring): the boundary answered with a typed HTTP 4xx/408/413/
    422/429/503/409 shape -- a BOUNDARY-level refusal, never a kernel write_verdict. `status` is
    the HTTP status; `body` is the boundary's own typed JSON shape (disposition/message and
    whatever else that shape carries) -- printed verbatim by the shim's own error path, never
    reworded (the boundary's own teach-text stays intact, spec §5: "surface as the shim's
    stderr with their teach-text")."""

    def __init__(self, status: int, body: Any) -> None:
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body


class ServedConfig:
    """The resolved (deployment_record, base_url_with_/d/segment) a rebased shim needs for every
    call it makes -- computed ONCE per invocation (ADR-0012 P1), never re-resolved per request."""

    def __init__(self, record: deployment_record.DeploymentRecord) -> None:
        self.record = record
        self.base = f"{record.boundary_url}/d/{record.boundary_deployment}"


def load_served_config(deployment_path: str | Path) -> ServedConfig:
    """The ONE place a rebased shim resolves `deployment.json` AND its two new served-transport
    keys, refusing loudly (never silently falling back to a guessed URL/deployment name) when
    either is absent -- spec §5's own words, verbatim."""
    try:
        record = deployment_record.load_deployment(deployment_path)
    except deployment_record.DeploymentError as e:
        raise BoundaryClientError(str(e)) from e
    missing = [k for k in ("boundary_url", "boundary_deployment")
               if getattr(record, k) is None]
    if missing:
        raise BoundaryClientError(
            f"deployment record at {deployment_path} is missing required-for-the-served-shim "
            f"field(s): {', '.join(missing)} (design/FABLE-BOUNDARY-MULTIPLEX-AND-CLI-REBASE-"
            f"SPEC.md §5: the rebased verbs need 'boundary_url' -- the served boundary's own "
            f"base URL -- and 'boundary_deployment' -- the /d/{{name}} segment this project "
            f"answers under -- both refused-if-absent, never guessed. Add both keys to "
            f"{deployment_path}, or run the ./legacy/ original instead.")
    return ServedConfig(record)


def _http(method: str, url: str, payload: dict | None = None, timeout: float = 65.0) -> tuple[int, Any]:
    """The ONE choke point every HTTP call in this module passes through (ADR-0012 P1) --
    `timeout` is deliberately a hair over `serving/boundary_service.py`'s own
    PSQL_EXEC_TIMEOUT_S=60 ceiling, so a genuinely-slow-but-answering boundary call is not cut
    off by this client before the boundary's OWN bound would have fired first. Raises
    `BoundaryUnreachable` (exit 4) on a connection-level failure -- never lets `urllib`'s own
    exception classes leak past this module's boundary."""
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body_bytes = resp.read()
            body = json.loads(body_bytes) if body_bytes else None
            return resp.status, body
    except urllib.error.HTTPError as e:
        body_bytes = e.read()
        try:
            body = json.loads(body_bytes) if body_bytes else None
        except json.JSONDecodeError:
            body = {"detail": body_bytes.decode("utf-8", errors="replace")}
        return e.code, body
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        raise BoundaryUnreachable(f"{e.__class__.__name__}: {e}") from e


# HTTP statuses this client treats as a TYPED BOUNDARY REFUSAL (exit 3) on a READ call -- every
# one of them is a shape `serving/boundary_service.py` itself mints (never a kernel verdict; read
# routes have no kernel-verdict concept at all, so ANY non-200 on a read is boundary-level).
_READ_REFUSAL_STATUSES = {404, 409, 413, 422, 429, 503}


def get_json(base: str, path: str, params: dict[str, Any] | None = None) -> Any:
    """A single GET, JSON-decoded. Raises `BoundaryRefusal` on any typed non-200 (every read
    route's own refusal shapes are boundary-level by construction -- see module docstring)."""
    url = base + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    status, body = _http("GET", url)
    if status != 200:
        raise BoundaryRefusal(status, body)
    return body


def get_all_rows(base: str, path: str, cursor: str = "after_id", limit: int = 1000) -> list[dict]:
    """Walks EVERY page of a paginated read route to completion, returning the full row list --
    the client-side half of spec's own "no server-side filter grammar in v1: shims filter
    client-side over paginated output" discipline. `cursor` is `after_id` (the id-keyed shape
    `/rows/current`, `/credited`, `/standing/principals`, `/rows/{id}/history`, and every
    id-keyed `/views/{view}` entry share) or `after_slug` (the keyset shape `/work/items` and
    every slug-keyed `/views/{view}` entry share) -- the caller names which, per
    `boundary_service.py`'s own `VIEW_REGISTRY` (never guessed here). The cursor's next value is
    read off the LAST row of each page -- the field name defaults to 'id' (for `after_id`) or
    'slug' (for `after_slug`), overridden per-path by `_ID_FIELD_OVERRIDE`/`_SLUG_FIELD_OVERRIDE`
    below for the handful of views/routes keyed on a differently-named column (never guessed;
    both dicts are this module's own disclosed duplication of `VIEW_REGISTRY`'s key-column
    choices, see their own comment)."""
    rows: list[dict] = []
    if cursor == "after_id":
        id_field = _ID_FIELD_OVERRIDE.get(path.rsplit("/", 1)[-1], "id")
        after_id = 0
        while True:
            page = get_json(base, path, {"after_id": after_id, "limit": limit})
            if not isinstance(page, list) or not page:
                break
            rows.extend(page)
            after_id = page[-1][id_field]
            if len(page) < limit:
                break
        return rows
    if cursor == "after_slug":
        slug_field = _SLUG_FIELD_OVERRIDE.get(path.rsplit("/", 1)[-1], "slug")
        after_slug = ""
        while True:
            page = get_json(base, path, {"after_slug": after_slug, "limit": limit})
            if not isinstance(page, list) or not page:
                break
            rows.extend(page)
            after_slug = page[-1][slug_field]
            if len(page) < limit:
                break
        return rows
    raise BoundaryClientError(f"get_all_rows: unrecognized cursor kind {cursor!r} (expected "
                              f"'after_id' or 'after_slug')")


# serving/boundary_service.py's own VIEW_REGISTRY is the enumeration authority for every view's
# key COLUMN NAME and KIND -- deliberately NOT imported here (`boundary_service` pulls in
# `fastapi`/`uvicorn`, dependencies this thin CLI client has no business requiring just to issue
# a GET; every rebased shim -- led/pickup/asof-export/distance-to-clean -- imports THIS module,
# not that one). The two override dicts below are a DELIBERATE, disclosed duplication of
# `VIEW_REGISTRY`'s own key-column choices (never its view NAMES or membership, which this
# client never needs to know in advance -- an unknown view name simply 404s, same as any other
# `BoundaryRefusal`) -- kept in sync by hand; a future view added to `VIEW_REGISTRY` with a
# key column other than 'id'/'slug' needs a matching entry here, named as a residual risk rather
# than silently assumed away.
_SLUG_FIELD_OVERRIDE: dict[str, str] = {"countersign_obligation": "scope"}  # work_item_violations/work_review_gap/work_item_current all key on the default 'slug'
_ID_FIELD_OVERRIDE: dict[str, str] = {
    "question_status": "question_id",
    "review_stamp_distinctness": "review_id",
    "model_attestations": "row_id",
    "model_defeated_rows": "attest_id",
}


def post_write(base: str, surface: str, payload: dict) -> tuple[int, dict]:
    """POSTs a write payload to `/write/{surface}`. Returns (exit_code, verdict_or_body) per the
    module docstring's exit-code convention -- 0/1 for a genuine kernel write_verdict (accepted/
    refused), never reached for a boundary-level refusal (that raises `BoundaryRefusal`, exit 3,
    to the CALLER -- this function itself never returns exit 3/4; see `write_and_report` below
    for the one place that maps an exception to a process exit code)."""
    status, body = _http("POST", f"{base}/write/{surface}", payload)
    if status != 200:
        raise BoundaryRefusal(status, body)
    if not isinstance(body, dict) or "disposition" not in body:
        raise BoundaryRefusal(status, body)  # a 200 with a non-verdict shape is still not a kernel verdict
    return (0 if body["disposition"] == "accepted" else 1), body


def write_and_report(base: str, surface: str, payload: dict, *, echo_row_id: bool = True) -> int:
    """The shim-facing convenience every rebased write call site uses (mirrors
    bootstrap/templates/led.tmpl's own `kernel_write()` printing convention byte-for-byte, spec
    §5: "same typed verdicts"): prints the accepted row id to stdout (silent when there is none,
    e.g. obligation_write), or the kernel's own refusal teach-text to stderr; returns the process
    exit code per this module's own convention. Boundary-level failures (`BoundaryRefusal`/
    `BoundaryUnreachable`) are NOT caught here -- the caller's own top-level dispatch catches
    them once, uniformly, so every rebased verb reports a boundary-vs-kernel refusal identically
    (ADR-0012 P1; see e.g. `led`'s own `_main` wrapper)."""
    exit_code, verdict = post_write(base, surface, payload)
    if exit_code == 0:
        row_id = verdict.get("row_id")
        if echo_row_id and row_id is not None:
            print(f"led: row {row_id} written.")
        return 0
    sys.stderr.write(
        f"led: REFUSED by the kernel write boundary (SQLSTATE {verdict.get('sqlstate')}; "
        f"journaled as write_refused row {verdict.get('refusal_id')} -- the refusal itself is "
        f"now a committed, hash-chained ledger record, s43):\n"
        f"  {verdict.get('message')}\n")
    return 1


def report_boundary_exception(prog: str, exc: Exception) -> int:
    """The ONE place a rebased shim's top-level dispatch turns a `BoundaryRefusal`/
    `BoundaryUnreachable`/`BoundaryClientError` into stderr text + an exit code (ADR-0012 P1) --
    spec §5: "The boundary's own refusals ... surface as the shim's stderr with their teach-text
    and a distinct nonzero exit code." Never reached for a genuine kernel write_verdict refusal
    (that path returns exit 1 through `write_and_report`/`post_write` directly, without ever
    raising)."""
    if isinstance(exc, BoundaryRefusal):
        # Two message-key conventions coexist on the boundary's own typed shapes: the NAMED
        # pydantic models (PayloadTooLarge/InfraFailure/UnknownView/...) carry "message"; the
        # ad hoc inline 422s this service's own read/write routes return for a single bound
        # check (e.g. the A5.2 write-body id-domain closure, A4.2's `_out_of_range_id`) carry
        # FastAPI's own conventional "detail" key instead -- both read here so neither shape's
        # teach-text is silently dropped to `None` (live-witnessed gap: an id-domain 422's own
        # detail text printed as literal "None" before this fix).
        message = None
        if isinstance(exc.body, dict):
            message = exc.body.get("message", exc.body.get("detail"))
        else:
            message = exc.body
        disposition = exc.body.get("disposition") if isinstance(exc.body, dict) else None
        sys.stderr.write(
            f"{prog}: REFUSED by the boundary SERVICE itself (HTTP {exc.status}"
            + (f", disposition={disposition!r}" if disposition else "") + ") -- "
            f"this is NOT a kernel verdict (no ledger write was attempted/journaled for this "
            f"call):\n  {message}\n")
        return 3
    if isinstance(exc, BoundaryUnreachable):
        sys.stderr.write(
            f"{prog}: REFUSED -- the boundary service itself could not be reached "
            f"({exc.detail}). Nothing was read or written. Is the boundary process running at "
            f"the deployment record's own boundary_url?\n")
        return 4
    if isinstance(exc, BoundaryClientError):
        sys.stderr.write(f"{prog}: REFUSED -- {exc}\n")
        return 4
    raise exc
