"""Debug (test) mode and test data, for super admins (v2.2).

- GET  /api/admin/test-mode                        state, pending test data, saved datasets
- POST /api/admin/test-mode/enable   {dataset?}    copy the real data aside, run on a copy
- POST /api/admin/test-mode/disable                back to the real data; the test data waits for a decision
- POST /api/admin/test-mode/pending/{id}  {action: save|delete, name?}
- GET  /api/admin/test-mode/{pending|dataset}/{id}/export.zip   CSV files in the sheets' format
- DELETE /api/admin/test-mode/datasets/{name}
- GET  /api/admin/test-data/schema                 the sheets
- POST /api/admin/test-data/generate  {seed, counts}   rows for the sheets (not saved)
- POST /api/admin/test-data/validate  {sheets}
- POST /api/admin/test-data/import    {sheets, simulate_activity, seed}
The test-data routes work only while debug mode is on.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from .. import gpc
from ..activity import log_activity
from ..database import get_db
from ..models import User
from ..policy import require
from ..services import dummy_data, sandbox, test_mode
from ..services.test_mode import TestModeError

router = APIRouter(prefix="/api/admin", tags=["test mode"])
SUPER = require("users.assign_role")


def _err(e: TestModeError):
    return HTTPException(e.status, {"code": e.code, "message": e.message})


def _policy_allows(flag: str, what: str):
    if not gpc.get(flag):
        raise HTTPException(403, {"code": "POLICY_DISABLED", "message": f"{what} is switched off by policy ({flag}): "
                                  "only root can change that (docs/design/gpc.md)"})


@router.get("/test-mode")
async def get_state(user: User = Depends(SUPER)):
    return {**test_mode.state(), "test_password": test_mode.test_password(),
            "policy": {"allowed": gpc.get("test_mode.allowed"), "forced": gpc.get("test_mode.forced"), "export_allowed": gpc.get("test_mode.export_allowed"),
                       "pending_ttl_hours": gpc.get("test_mode.pending_ttl_hours"),
                       "dataset_ttl_days": gpc.get("test_mode.dataset_ttl_days")}}


class Enable(BaseModel):
    dataset: str | None = None


@router.post("/test-mode/enable")
async def enable(body: Enable, request: Request, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    _policy_allows("test_mode.allowed", "Debug mode")
    try:
        st = await test_mode.enable(user, getattr(request.state, "session", None), body.dataset)
    except TestModeError as e:
        raise _err(e)
    await log_activity(db, "system.test_mode_on", user.id, "system", None, {"flag": True, "dataset": body.dataset})
    await db.commit()
    return st


@router.post("/test-mode/disable")
async def disable(request: Request, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    try:
        st = await test_mode.disable(user, getattr(request.state, "session", None))
    except TestModeError as e:
        raise _err(e)
    from ..database import async_session
    async with async_session() as fresh:                 # the real database again
        await log_activity(fresh, "system.test_mode_off", user.id, "system", None, {"flag": True,
                           "pending": st.get("pending_id")})
        await fresh.commit()
    return st


class PendingAction(BaseModel):
    action: str
    name: str = ""


@router.post("/test-mode/pending/{pid}")
async def decide(pid: str, body: PendingAction, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    try:
        if body.action == "save":
            saved = test_mode.save_pending(pid, body.name.strip(), user.username)
            await log_activity(db, "system.test_data_save", user.id, "system", None, {"flag": True, "dataset": saved["name"]})
            await db.commit()
            return saved
        if body.action == "delete":
            test_mode.delete_pending(pid)
            await log_activity(db, "system.test_data_delete", user.id, "system", None, {"flag": True, "pending": pid})
            await db.commit()
            return {"status": "deleted"}
    except TestModeError as e:
        raise _err(e)
    raise HTTPException(422, "action must be save or delete")


@router.get("/test-mode/{kind}/{ident}/export.zip")
async def export(kind: str, ident: str, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    if kind not in ("pending", "dataset"):
        raise HTTPException(404, "Not found")
    _policy_allows("test_mode.export_allowed", "Exporting test data")
    try:
        data = test_mode.export_zip(test_mode.file_for(kind, ident))
    except TestModeError as e:
        raise _err(e)
    await log_activity(db, "system.test_data_export", user.id, "system", None, {"flag": True, "kind": kind, "name": ident})
    await db.commit()
    return Response(data, media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="impress-test-data-{ident}.zip"'})


@router.delete("/test-mode/datasets/{name}")
async def delete_dataset(name: str, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    try:
        test_mode.delete_dataset(name)
    except TestModeError as e:
        raise _err(e)
    await log_activity(db, "system.test_data_delete", user.id, "system", None, {"flag": True, "dataset": name})
    await db.commit()
    return {"status": "deleted"}


def _require_on():
    _policy_allows("test_mode.allowed", "Test data")
    if not test_mode.state()["on"]:
        raise HTTPException(409, {"code": "TEST_MODE_OFF",
                                  "message": "Turn on debug mode first: test data never goes into the real database."})


@router.get("/test-data/schema")
async def schema(user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    return {"sheets": sandbox.SHEETS, "defaults": dummy_data.DEFAULT_COUNTS, "limits": dummy_data.LIMITS,
            "counts": await sandbox.table_counts(db), "test_mode": test_mode.state()["on"]}


class Generate(BaseModel):
    seed: int = Field(1, ge=0, le=2**31)
    counts: dict = {}


@router.post("/test-data/generate")
async def generate(body: Generate, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    _require_on()
    sheets = dummy_data.generate(body.seed, body.counts, await sandbox.taken_values(db))
    return {"seed": body.seed, "sheets": sheets}


class Sheets(BaseModel):
    sheets: dict
    simulate_activity: bool = True
    seed: int = 1


@router.post("/test-data/validate")
async def validate(body: Sheets, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    _require_on()
    return await sandbox.validate(db, body.sheets)


@router.post("/test-data/import")
async def import_(body: Sheets, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    _require_on()
    report = await sandbox.import_sheets(db, body.sheets, user, body.simulate_activity, body.seed)
    if not report.get("ok"):
        await db.rollback()
        raise HTTPException(422, {"code": "INVALID_ROWS", "message": "Some rows need fixing", "errors": report["errors"]})
    await log_activity(db, "system.test_data_import", user.id, "system", None,
                       {"imported": report["imported"], "activity": report["activity"]})
    await db.commit()
    return report
