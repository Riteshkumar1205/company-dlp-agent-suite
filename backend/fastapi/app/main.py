#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import uuid, os, json, logging
from . import db, storage, schemas, auth, alerting, devices as devices_mod, otp, policy, update, config

logger = logging.getLogger("uvicorn")
app = FastAPI(title="Company DLP Collector")

STORAGE = Path(os.getenv("STORAGE_PATH", "./data/uploads"))
STORAGE.mkdir(parents=True, exist_ok=True)

@app.on_event("startup")
def startup():
    db.init_db(os.getenv("DATABASE_URL", "sqlite:///./data/collector.db"))
    storage.ensure_storage_dir(STORAGE)

@app.post("/api/v1/events")
async def receive_event(payload: dict, request: Request):
    try:
        event_id = payload.get("event_id") or f"evt-{uuid.uuid4().hex[:12]}"
        storage_path = storage.event_json_save(STORAGE, event_id, payload)
        db.create_event(db.get_sync_session(), event_id, payload, str(storage_path))
        # alert if needed
        try:
            alerting.alert_admin(payload)
        except Exception:
            logger.exception("alerting failed")
        return {"status":"ok", "id": event_id}
    except Exception as e:
        logger.exception("receive_event failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/events/{event_id}/thumbnail")
async def receive_thumbnail(event_id: str, thumbnail: UploadFile = File(...)):
    try:
        ext = Path(thumbnail.filename).suffix or ".png"
        out_path = STORAGE / f"{event_id}_thumb{ext}"
        await storage.save_upload_async(thumbnail, out_path)
        db.attach_thumbnail(db.get_sync_session(), event_id, str(out_path))
        return {"status":"ok", "id": event_id}
    except Exception as e:
        logger.exception("thumbnail upload failed")
        raise HTTPException(status_code=500, detail=str(e))

# commands endpoints for agents
@app.get("/api/v1/agents/{device_id}/commands")
def poll_commands(device_id: str):
    try:
        return db.fetch_and_mark_delivered(db.get_sync_session(), device_id)
    except Exception:
        logger.exception("poll commands failed")
        raise HTTPException(status_code=500, detail="poll error")

@app.post("/api/v1/agents/{device_id}/commands")
def create_command(device_id: str, cmd: schemas.CommandCreate, user=Depends(auth.admin_required)):
    try:
        cmd_id = db.enqueue_command(db.get_sync_session(), device_id, cmd.type, cmd.payload or {})
        return {"status":"ok", "id": cmd_id}
    except Exception:
        logger.exception("create command failed")
        raise HTTPException(status_code=500, detail="enqueue error")

# OTP & onboarding endpoints
@app.post("/api/v1/register_device")
def register_device(payload: dict):
    email = payload.get("employee_email")
    requested_id = payload.get("device_id")
    meta = payload.get("metadata", {})
    if not email:
        raise HTTPException(status_code=400, detail="email required")
    device_id = devices_mod.register_device(email, requested_device_id=requested_id, metadata=meta)
    return {"device_id": device_id}

@app.post("/api/v1/request_otp")
def request_otp(payload: dict):
    email = payload.get("email")
    device_id = payload.get("device_id")
    if not email or not device_id:
        raise HTTPException(status_code=400, detail="missing fields")
    sent = otp.request_otp(email, device_id, config.SMTP_CONFIG)
    return {"sent": bool(sent)}

@app.post("/api/v1/verify_otp")
def verify_otp(payload: dict):
    device_id = payload.get("device_id")
    code = payload.get("code")
    if not device_id or code is None:
        raise HTTPException(status_code=400, detail="missing")
    ok = otp.verify_otp(device_id, code)
    if ok:
        devices_mod.activate_device(device_id)
    return {"ok": ok}

# Policy and update endpoints
@app.get("/api/v1/policy")
def get_policy():
    return policy.load_policy()

# include admin router
from . import admin
app.include_router(admin.router)
# include update router
from . import update as update_module
app.include_router(update_module.router)
