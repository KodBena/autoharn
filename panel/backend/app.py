# >>> PROVENANCE-STAMP >>> (auto; tools/hooks/stamp_provenance.py — do not hand-edit)
#   first-seen : 2026-07-14T23:23:56Z
#   last-change: 2026-07-14T23:24:05Z
#   contributors: a857c93d/main
# <<< PROVENANCE-STAMP <<<

"""panel.backend.app — the FastAPI service implementing the API contract (spec S3).

Bound to 127.0.0.1 only (standing ruling: no host-hardening ceremony for a localhost tool on
the maintainer's own machine). Reads go through `ledger_read.py` (pure SELECTs); the ONLY write
route, `/api/cosign`, shells to `./led review` via `cosign.py` -- never a parallel write path.

Run directly: `python3 -m uvicorn app:app --host 127.0.0.1 --port <config.DEFAULT_BIND_PORT>`
from this directory (see panel/README.md, WP-D, for the operator walkthrough).
"""
from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import cosign
import ledger_read
import manifest_load
from config import PanelConfig, load_config
from disposition import derive_status


class Broadcaster:
    """Fan-out from ONE background DB poll to N connected SSE clients (spec S4) -- not one poll
    per client. A plain set of per-client asyncio.Queues; publish pushes to every live one."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    async def publish(self, event: dict[str, Any]) -> None:
        for q in list(self._subscribers):
            await q.put(event)


class AppState:
    def __init__(self, cfg: PanelConfig) -> None:
        self.cfg = cfg
        self.broadcaster = Broadcaster()
        self.poll_task: asyncio.Task | None = None


async def _poll_loop(state: AppState) -> None:
    """The ONE background task polling `SELECT max(id), max(ts), count(*) FROM ledger` every
    `cfg.poll_interval` (spec S4's resolved tradeoff: no NOTIFY exists on this ledger's writes,
    and minting one means editing a frozen kernel/template surface -- polling is the only
    mechanism that respects that constraint). Publishes to every subscribed SSE client only when
    the watermark actually moves."""
    last: dict[str, Any] | None = None
    while True:
        try:
            wm = await asyncio.to_thread(ledger_read.watermark, state.cfg)
        except Exception:  # noqa: BLE001 -- a transient DB hiccup must not kill the poller
            await asyncio.sleep(state.cfg.poll_interval)
            continue
        if wm != last:
            last = wm
            await state.broadcaster.publish({"type": "ledger-change", "watermark": wm})
        await asyncio.sleep(state.cfg.poll_interval)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    cfg = load_config()
    state = AppState(cfg)
    app.state.panel = state
    # Startup: ensure the maintainer principal is registered (idempotent -- ON CONFLICT DO
    # NOTHING at the kernel), so the first co-sign never fails on an unregistered actor (spec S5).
    result = await asyncio.to_thread(
        cosign.ensure_principal_registered, cfg, cfg.maintainer_principal, "human"
    )
    if not result.ok:
        raise RuntimeError(
            f"panel startup: could not register maintainer principal {cfg.maintainer_principal!r} "
            f"via ./led register-principal (exit {result.exit_code}): {result.stderr}"
        )
    state.poll_task = asyncio.create_task(_poll_loop(state))
    try:
        yield
    finally:
        if state.poll_task is not None:
            state.poll_task.cancel()


app = FastAPI(title="autoharn maintainer co-sign panel", lifespan=lifespan)


def _state(app_: FastAPI) -> AppState:
    return app_.state.panel  # type: ignore[no-any-return]


@app.get("/api/health")
def api_health() -> dict[str, Any]:
    cfg = _state(app).cfg
    return ledger_read.health(cfg)


@app.get("/api/commission/{manifest_id}")
def api_commission(manifest_id: str) -> dict[str, Any]:
    cfg = _state(app).cfg
    try:
        manifest = manifest_load.load_manifest(cfg.manifests_dir, manifest_id)
    except manifest_load.ManifestError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    commission_row = ledger_read.ledger_row(cfg, manifest.commission_row)

    items_out: list[dict[str, Any]] = []
    for item in manifest.items:
        resolved_witnesses = ledger_read.resolve_item_witnesses(cfg, item)
        status = derive_status([rw.facts for rw in resolved_witnesses])
        items_out.append(
            {
                "id": item.id,
                "parent": item.parent,
                "label": item.label,
                "text": item.text,
                "status": status,
                "witnesses": [
                    {
                        "ref_kind": rw.ref_kind,
                        "ref": rw.ref,
                        "note": rw.note,
                        "resolved": rw.resolved,
                        "cosign_target_row": rw.cosign_target_row,
                        "cosign": rw.cosign,
                    }
                    for rw in resolved_witnesses
                ],
            }
        )

    return {
        "manifest_id": manifest.manifest_id,
        "commission_row": manifest.commission_row,
        "title": manifest.title,
        "commission_row_facts": commission_row,
        "items": items_out,
    }


@app.get("/api/ledger/recent")
def api_ledger_recent(n: int = 50) -> list[dict[str, Any]]:
    cfg = _state(app).cfg
    return ledger_read.recent_ledger(cfg, n)


@app.get("/api/work")
def api_work() -> list[dict[str, Any]]:
    cfg = _state(app).cfg
    return ledger_read.work_items(cfg)


@app.get("/api/review-gap")
def api_review_gap() -> list[dict[str, Any]]:
    cfg = _state(app).cfg
    return ledger_read.review_gap(cfg)


@app.get("/api/questions")
def api_questions() -> list[dict[str, Any]]:
    cfg = _state(app).cfg
    return ledger_read.question_status(cfg)


@app.get("/api/watermark")
def api_watermark() -> dict[str, Any]:
    cfg = _state(app).cfg
    return ledger_read.watermark(cfg)


@app.get("/api/events")
async def api_events() -> StreamingResponse:
    state = _state(app)
    queue = state.broadcaster.subscribe()

    async def gen() -> AsyncIterator[bytes]:
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n".encode()
        finally:
            state.broadcaster.unsubscribe(queue)

    return StreamingResponse(gen(), media_type="text/event-stream")


class CosignRequest(BaseModel):
    row_id: int
    verdict: str
    independence: str
    basis: str


@app.post("/api/cosign")
def api_cosign(req: CosignRequest) -> dict[str, Any]:
    cfg = _state(app).cfg
    try:
        result = cosign.cosign(cfg, req.row_id, req.verdict, req.independence, req.basis)
    except cosign.CosignValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "ok": result.ok,
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "review_id": result.review_id,
    }
